from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user
from app.logging_config import logger
from app.models.role import Role
from app.models.user import User
from app.rate_limit import client_ip, login_rate_limiter
from app.schemas.auth import ChangePasswordRequest, LoginRequest, MeResponse, TokenResponse
from app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    retry_after = login_rate_limiter.retry_after(ip, payload.username)
    if retry_after is not None:
        logger.warning("Rate-limited login attempt for %r from %s", payload.username, ip)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        login_rate_limiter.record_failure(ip, payload.username)
        logger.warning("Failed login for %r from %s", payload.username, ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    login_rate_limiter.reset(ip, payload.username)
    role = db.get(Role, user.role_id)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        user_id=user.user_id,
        role_name=role.role_name,
        assigned_class_name=user.assigned_class_name,
    )
    return TokenResponse(
        access_token=token, role=role.role_name, assigned_class_name=user.assigned_class_name
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, current_user.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return MeResponse(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        role=current_user.role_name,
        assigned_class_name=current_user.assigned_class_name,
    )


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lets any signed-in user change their own password after confirming the
    current one — so the bootstrap admin can move off the default credentials."""
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "New password must be at least 8 characters.")
    user = db.get(User, current_user.user_id)
    if user is None or not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password changed successfully."}
