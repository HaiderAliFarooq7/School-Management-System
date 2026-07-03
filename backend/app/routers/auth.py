from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.master import MasterSessionLocal, MasterUser, UserDirectory
from app.db.session import get_db
from app.db.tenants import default_school_id, school_info, tenant_session
from app.deps import CurrentUser, get_current_user
from app.logging_config import logger
from app.models.role import Role
from app.models.user import User
from app.rate_limit import client_ip, login_rate_limiter
from app.schemas.auth import ChangePasswordRequest, LoginRequest, MeResponse, TokenResponse
from app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _school_label(school_id: int | None) -> tuple[str, str]:
    info = school_info(school_id) if school_id is not None else None
    if not info:
        return "", ""
    return info["school_name"], info["campus_name"]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    """Multi-tenant login.

    1. Super admin — lives only in the master database; signs in with the
       default school selected (switchable afterwards).
    2. School staff — the master user-directory routes the username to its
       school; the password is then verified against that school's own
       database (the single source of truth for tenant credentials).
    3. Fallback — usernames not in the directory are tried against the
       default school, which keeps pre-conversion accounts and test
       fixtures working; a successful login self-heals the directory.
    """
    ip = client_ip(request)
    username = payload.username.strip()
    retry_after = login_rate_limiter.retry_after(ip, username)
    if retry_after is not None:
        logger.warning("Rate-limited login attempt for %r from %s", username, ip)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    def reject():
        login_rate_limiter.record_failure(ip, username)
        logger.warning("Failed login for %r from %s", username, ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    mdb = MasterSessionLocal()
    try:
        master_user = mdb.execute(
            select(MasterUser).where(MasterUser.username == username)
        ).scalar_one_or_none()
        if master_user is not None:
            if not master_user.is_active or not verify_password(payload.password, master_user.password_hash):
                reject()
            login_rate_limiter.reset(ip, username)
            sid = default_school_id()
            school_name, campus_name = _school_label(sid)
            token = create_access_token(
                user_id=master_user.id, role_name="Admin", assigned_class_name=None,
                school_id=sid, is_super=True,
            )
            logger.info("Super admin %r logged in from %s", username, ip)
            return TokenResponse(
                access_token=token, role="Admin", assigned_class_name=None,
                school_id=sid, school_name=school_name, campus_name=campus_name, is_super=True,
            )

        directory_row = mdb.execute(
            select(UserDirectory).where(UserDirectory.username == username)
        ).scalar_one_or_none()
    finally:
        mdb.close()

    school_id = directory_row.school_id if directory_row else default_school_id()
    if school_id is None:
        reject()
    info = school_info(school_id)
    if info is None:
        reject()
    if info["status"] != "active":
        login_rate_limiter.record_failure(ip, username)
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This school is currently disabled. Contact the system administrator.",
        )

    db = tenant_session(school_id)
    try:
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            reject()

        login_rate_limiter.reset(ip, username)
        role = db.get(Role, user.role_id)
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        role_name = role.role_name
        assigned = user.assigned_class_name
        user_id = user.user_id
    finally:
        db.close()

    if directory_row is None:
        # Self-heal the routing directory for accounts that predate the
        # multi-tenant conversion (they resolved via the default school).
        mdb = MasterSessionLocal()
        try:
            if mdb.execute(select(UserDirectory).where(UserDirectory.username == username)).scalar_one_or_none() is None:
                mdb.add(UserDirectory(username=username, school_id=school_id))
                mdb.commit()
        finally:
            mdb.close()

    school_name, campus_name = _school_label(school_id)
    token = create_access_token(
        user_id=user_id, role_name=role_name, assigned_class_name=assigned, school_id=school_id,
    )
    return TokenResponse(
        access_token=token, role=role_name, assigned_class_name=assigned,
        school_id=school_id, school_name=school_name, campus_name=campus_name, is_super=False,
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_super:
        mdb = MasterSessionLocal()
        try:
            mu = mdb.get(MasterUser, current_user.user_id)
        finally:
            mdb.close()
        if mu is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return MeResponse(
            user_id=mu.id, username=mu.username, full_name=mu.name or "Super Administrator",
            role="Admin", assigned_class_name=None,
        )
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
    if current_user.is_super:
        mdb = MasterSessionLocal()
        try:
            mu = mdb.get(MasterUser, current_user.user_id)
            if mu is None or not verify_password(payload.current_password, mu.password_hash):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
            mu.password_hash = hash_password(payload.new_password)
            mdb.commit()
        finally:
            mdb.close()
        return {"detail": "Password changed successfully."}
    user = db.get(User, current_user.user_id)
    if user is None or not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password changed successfully."}
