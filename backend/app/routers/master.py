"""Super-admin control plane: manage schools, switch between them, see
system-wide statistics. Every endpoint requires the global super admin."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.master import School, UserDirectory, get_master_db
from app.db.tenants import (
    dispose_engine_for,
    refresh_registry_from_master,
    school_info,
    tenant_session,
)
from app.deps import CurrentUser, require_super_admin
from app.logging_config import logger
from app.models.role import Role
from app.models.student import Student
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password
from app.services.provisioning import provision_school

router = APIRouter(
    prefix="/api/master", tags=["master"], dependencies=[Depends(require_super_admin)]
)

VALID_STATUSES = {"active", "disabled", "archived"}


class SchoolOut(BaseModel):
    school_id: int
    school_name: str
    campus_name: str
    database_name: str
    database_status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SchoolCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=255)
    campus_name: str = Field(default="", max_length=255)
    database_name: str = Field(min_length=3, max_length=63)
    admin_username: str = Field(min_length=3, max_length=50)
    admin_password: str = Field(min_length=8)


class StatusUpdate(BaseModel):
    database_status: str


class ResetAdminPassword(BaseModel):
    username: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class SchoolStats(BaseModel):
    school_id: int
    active_students: int
    total_students: int
    users: int
    reachable: bool


@router.get("/schools", response_model=list[SchoolOut])
def list_schools(mdb: Session = Depends(get_master_db)):
    return mdb.execute(select(School).order_by(School.school_id)).scalars().all()


@router.post("/schools", response_model=SchoolOut, status_code=status.HTTP_201_CREATED)
def create_school(payload: SchoolCreate, mdb: Session = Depends(get_master_db)):
    """Creates the database, migrates it, seeds roles + the school Admin, and
    registers everything — one click, fully automatic."""
    try:
        return provision_school(
            mdb,
            school_name=payload.school_name,
            campus_name=payload.campus_name,
            database_name=payload.database_name,
            admin_username=payload.admin_username,
            admin_password=payload.admin_password,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except Exception:
        logger.exception("School provisioning failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "School creation failed — check the server logs. Nothing destructive happened; "
            "retrying with the same details is safe.",
        )


@router.patch("/schools/{school_id}/status", response_model=SchoolOut)
def set_school_status(school_id: int, payload: StatusUpdate, mdb: Session = Depends(get_master_db)):
    """active — normal; disabled — logins and API access blocked; archived —
    hidden and blocked, but the physical database is retained for recovery."""
    if payload.database_status not in VALID_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Status must be one of {sorted(VALID_STATUSES)}.")
    school = mdb.get(School, school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    school.database_status = payload.database_status
    mdb.commit()
    if payload.database_status != "active":
        dispose_engine_for(school_id)
    refresh_registry_from_master()
    logger.info("School %s status -> %s", school_id, payload.database_status)
    return school


@router.delete("/schools/{school_id}", response_model=SchoolOut)
def delete_school(school_id: int, mdb: Session = Depends(get_master_db)):
    """'Delete' archives: login is blocked and the school disappears from
    active lists, but the physical database is deliberately NOT dropped."""
    school = mdb.get(School, school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    school.database_status = "archived"
    mdb.commit()
    dispose_engine_for(school_id)
    refresh_registry_from_master()
    logger.warning("School %s (%s) archived by super admin", school_id, school.school_name)
    return school


@router.post("/schools/{school_id}/reset-admin-password")
def reset_school_admin_password(
    school_id: int, payload: ResetAdminPassword, mdb: Session = Depends(get_master_db)
):
    """Resets any user's password inside the given school — the recovery path
    when a school admin locks themselves out."""
    if mdb.get(School, school_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    db = tenant_session(school_id)
    try:
        user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"No user '{payload.username}' in this school.")
        user.password_hash = hash_password(payload.new_password)
        db.commit()
    finally:
        db.close()
    logger.warning("Super admin reset password for %r in school %s", payload.username, school_id)
    return {"detail": f"Password for '{payload.username}' has been reset."}


@router.get("/schools/{school_id}/stats", response_model=SchoolStats)
def school_stats(school_id: int, mdb: Session = Depends(get_master_db)):
    if school_info(school_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    try:
        db = tenant_session(school_id)
        try:
            active = db.execute(
                select(func.count()).select_from(Student).where(Student.status == "Active")
            ).scalar_one()
            total = db.execute(select(func.count()).select_from(Student)).scalar_one()
            users = db.execute(select(func.count()).select_from(User)).scalar_one()
        finally:
            db.close()
        return SchoolStats(school_id=school_id, active_students=active, total_students=total, users=users, reachable=True)
    except Exception:
        logger.exception("Stats query failed for school %s", school_id)
        return SchoolStats(school_id=school_id, active_students=0, total_students=0, users=0, reachable=False)


@router.post("/switch/{school_id}")
def switch_school(school_id: int, current_user: CurrentUser = Depends(require_super_admin)):
    """Re-issues the super admin's JWT pinned to another school. Only the
    super admin has this endpoint — school staff tokens are permanently
    bound to their own school."""
    info = school_info(school_id)
    if info is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    if info["status"] == "archived":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This school is archived.")
    token = create_access_token(
        user_id=current_user.user_id, role_name="Admin", assigned_class_name=None,
        school_id=school_id, is_super=True,
    )
    logger.info("Super admin switched to school %s", school_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "Admin",
        "school_id": school_id,
        "school_name": info["school_name"],
        "campus_name": info["campus_name"],
        "is_super": True,
    }


@router.get("/stats")
def system_stats(mdb: Session = Depends(get_master_db)):
    """System-wide overview for the super admin dashboard."""
    schools = mdb.execute(select(School)).scalars().all()
    by_status: dict[str, int] = {}
    for s in schools:
        by_status[s.database_status] = by_status.get(s.database_status, 0) + 1
    directory_users = mdb.execute(select(func.count()).select_from(UserDirectory)).scalar_one()
    return {
        "total_schools": len(schools),
        "schools_by_status": by_status,
        "routed_usernames": directory_users,
    }
