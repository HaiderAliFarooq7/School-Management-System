from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.parent_account import ParentAccount
from app.models.user import User
from app.services.auth_service import decode_access_token
from app.services.parent_auth_service import decode_parent_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
parent_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/parent/login")


class CurrentUser:
    def __init__(
        self,
        user_id: int,
        role_name: str,
        assigned_class_name: str | None,
        school_id: int | None = None,
        is_super: bool = False,
    ):
        self.user_id = user_id
        self.role_name = role_name
        self.assigned_class_name = assigned_class_name
        self.school_id = school_id
        self.is_super = is_super


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentUser:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    school_id = payload.get("school_id")
    is_super = bool(payload.get("is_super"))

    if is_super:
        # The super admin lives in the master database, not in any school's
        # user_account table — validate there. Inside a school they act with
        # the Admin role, so every existing require_role("Admin") guard works.
        from app.db.master import MasterSessionLocal, MasterUser

        mdb = MasterSessionLocal()
        try:
            master_user = mdb.execute(
                select(MasterUser).where(MasterUser.id == user_id)
            ).scalar_one_or_none()
        finally:
            mdb.close()
        if master_user is None or not master_user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
        return CurrentUser(user_id, payload["role"], None, school_id, is_super=True)

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return CurrentUser(
        user.user_id, payload["role"], payload.get("assigned_class_name"), school_id
    )


def require_role(*allowed_roles: str):
    def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role_name not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role for this action")
        return current_user

    return checker


def require_super_admin(request: Request, token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Master-API guard: only the global super admin. Deliberately does NOT
    depend on get_db — master endpoints must work even when no tenant
    database is reachable."""
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if not payload.get("is_super"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Super admin access required")

    from app.db.master import MasterSessionLocal, MasterUser

    mdb = MasterSessionLocal()
    try:
        master_user = mdb.execute(
            select(MasterUser).where(MasterUser.id == user_id)
        ).scalar_one_or_none()
    finally:
        mdb.close()
    if master_user is None or not master_user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return CurrentUser(user_id, "SuperAdmin", None, payload.get("school_id"), is_super=True)


class CurrentParent:
    def __init__(self, parent_id: int, mobile_number: str, school_id: int | None):
        self.parent_id = parent_id
        self.mobile_number = mobile_number
        self.school_id = school_id


def get_current_parent(
    token: str = Depends(parent_oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentParent:
    """Auth dependency for parent-app endpoints. Rejects staff tokens: a valid
    token must carry ``type=parent``. The signed ``school_id`` claim has already
    routed ``db`` (via get_db) to the parent's own school database, so the
    parent_account lookup below is automatically tenant-scoped."""
    try:
        payload = decode_parent_access_token(token)
        parent_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    parent = db.get(ParentAccount, parent_id)
    if parent is None or not parent.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Parent account not found or inactive")

    return CurrentParent(parent.parent_id, parent.mobile_number, payload.get("school_id"))


def scope_class_filter(current_user: CurrentUser, requested_class_name: str | None) -> str | None:
    """Teachers may access any class (e.g. to cover attendance for a colleague);
    when they don't specify one, default to their own assigned class."""
    if current_user.role_name == "Teacher" and not requested_class_name:
        return current_user.assigned_class_name
    return requested_class_name
