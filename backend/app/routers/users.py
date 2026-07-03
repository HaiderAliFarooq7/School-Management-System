from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete as sa_delete, select, update
from sqlalchemy.orm import Session

from app.db.master import MasterSessionLocal, MasterUser, UserDirectory
from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.attendance import AttendanceRecord
from app.models.role import Role
from app.models.user import User
from app.schemas.user import PasswordResetRequest, UserCreate, UserOut, UserUpdate
from app.services.auth_service import hash_password

router = APIRouter(
    prefix="/api/users", tags=["users"], dependencies=[Depends(require_role("Admin"))]
)


def _assert_username_available(username: str, school_id: int | None) -> None:
    """Usernames must be unique across the whole platform — the master
    directory routes logins by username alone, so a name already used by
    another school (or the super admin) must be rejected here."""
    mdb = MasterSessionLocal()
    try:
        if mdb.execute(select(MasterUser).where(MasterUser.username == username)).scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "This username is reserved.")
        row = mdb.execute(
            select(UserDirectory).where(UserDirectory.username == username)
        ).scalar_one_or_none()
        if row is not None and row.school_id != school_id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This username is already used by another school — choose a different one.",
            )
    finally:
        mdb.close()


def _sync_directory(username: str, school_id: int | None, *, old_username: str | None = None, remove: bool = False) -> None:
    """Keeps the master login directory in step with tenant user changes."""
    if school_id is None:
        return
    mdb = MasterSessionLocal()
    try:
        if old_username and old_username != username:
            mdb.execute(sa_delete(UserDirectory).where(
                UserDirectory.username == old_username, UserDirectory.school_id == school_id
            ))
        if remove:
            mdb.execute(sa_delete(UserDirectory).where(
                UserDirectory.username == username, UserDirectory.school_id == school_id
            ))
        else:
            existing = mdb.execute(
                select(UserDirectory).where(UserDirectory.username == username)
            ).scalar_one_or_none()
            if existing is None:
                mdb.add(UserDirectory(username=username, school_id=school_id))
        mdb.commit()
    finally:
        mdb.close()


def _to_out(user: User, role_name: str) -> UserOut:
    return UserOut(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        role_name=role_name,
        assigned_class_name=user.assigned_class_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    rows = db.execute(select(User, Role).join(Role, Role.role_id == User.role_id)).all()
    return [_to_out(u, r.role_name) for u, r in rows]


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    role = db.execute(select(Role).where(Role.role_name == payload.role_name)).scalar_one_or_none()
    if role is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")
    existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    _assert_username_available(payload.username, current_user.school_id)

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role_id=role.role_id,
        assigned_class_name=payload.assigned_class_name,
    )
    db.add(user)
    db.commit()
    _sync_directory(payload.username, current_user.school_id)
    return _to_out(user, role.role_name)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    old_username = user.username
    if payload.username is not None and payload.username != user.username:
        existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
        _assert_username_available(payload.username, current_user.school_id)
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.assigned_class_name is not None:
        user.assigned_class_name = payload.assigned_class_name
    if payload.password:
        user.password_hash = hash_password(payload.password)
    role_name = None
    if payload.role_name is not None:
        role = db.execute(select(Role).where(Role.role_name == payload.role_name)).scalar_one_or_none()
        if role is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")
        user.role_id = role.role_id
        role_name = role.role_name
    db.commit()
    _sync_directory(user.username, current_user.school_id, old_username=old_username)

    if role_name is None:
        role_name = db.get(Role, user.role_id).role_name
    return _to_out(user, role_name)


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = False
    db.commit()
    role_name = db.get(Role, user.role_id).role_name
    return _to_out(user, role_name)


@router.patch("/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = True
    db.commit()
    role_name = db.get(Role, user.role_id).role_name
    return _to_out(user, role_name)


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password reset"}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """Admin-only hard delete. You can't delete the account you're currently
    logged in as. Any attendance records this user marked are kept, with
    'marked by' cleared rather than being deleted along with the account."""
    if user_id == current_user.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete the account you're logged in as.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    db.execute(update(AttendanceRecord).where(AttendanceRecord.marked_by_user_id == user_id).values(marked_by_user_id=None))
    username = user.username
    db.delete(user)
    db.commit()
    _sync_directory(username, current_user.school_id, remove=True)
    return {"detail": "Deleted"}
