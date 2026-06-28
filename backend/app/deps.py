from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class CurrentUser:
    def __init__(self, user_id: int, role_name: str, assigned_class_name: str | None):
        self.user_id = user_id
        self.role_name = role_name
        self.assigned_class_name = assigned_class_name


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentUser:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return CurrentUser(user.user_id, payload["role"], payload.get("assigned_class_name"))


def require_role(*allowed_roles: str):
    def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role_name not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role for this action")
        return current_user

    return checker


def scope_class_filter(current_user: CurrentUser, requested_class_name: str | None) -> str | None:
    """Teachers are restricted to their own assigned class regardless of what they request."""
    if current_user.role_name == "Teacher":
        if requested_class_name and requested_class_name != current_user.assigned_class_name:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized for this class")
        return current_user.assigned_class_name
    return requested_class_name
