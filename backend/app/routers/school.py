from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import LOGO_DIR
from app.db.session import get_db
from app.deps import require_role
from app.models.school import School
from app.schemas.school import CommunicationSettingsUpdate, NotificationSettingsUpdate, SchoolOut, SchoolUpdate

router = APIRouter(prefix="/api/school", tags=["school"])

ALLOWED_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_LOGO_BYTES = 5 * 1024 * 1024  # 5MB


def _get_or_create(db: Session) -> School:
    school = db.execute(select(School).limit(1)).scalar_one_or_none()
    if school is None:
        school = School()
        db.add(school)
        db.commit()
    return school


@router.get("", response_model=SchoolOut)
def get_school(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("", response_model=SchoolOut, dependencies=[Depends(require_role("Admin"))])
def update_school(payload: SchoolUpdate, db: Session = Depends(get_db)):
    school = _get_or_create(db)
    for field, value in payload.model_dump().items():
        setattr(school, field, value)
    db.commit()
    return school


@router.put(
    "/notification-settings",
    response_model=SchoolOut,
    dependencies=[Depends(require_role("Admin"))],
)
def update_notification_settings(payload: NotificationSettingsUpdate, db: Session = Depends(get_db)):
    school = _get_or_create(db)
    for field, value in payload.model_dump().items():
        setattr(school, field, value)
    db.commit()
    return school


@router.put(
    "/communication-settings",
    response_model=SchoolOut,
    dependencies=[Depends(require_role("Admin"))],
)
def update_communication_settings(payload: CommunicationSettingsUpdate, db: Session = Depends(get_db)):
    school = _get_or_create(db)
    for field, value in payload.model_dump().items():
        setattr(school, field, value)
    db.commit()
    return school


@router.post("/logo", response_model=SchoolOut, dependencies=[Depends(require_role("Admin"))])
async def upload_logo(file: UploadFile, db: Session = Depends(get_db)):
    suffix = Path(file.filename or "logo.png").suffix.lower() or ".png"
    if suffix not in ALLOWED_LOGO_SUFFIXES or not (file.content_type or "").startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please upload an image file (PNG, JPG, GIF, or WEBP).")

    dest = LOGO_DIR / f"school_logo{suffix}"
    written = 0
    try:
        with dest.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_LOGO_BYTES:
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        f"Logo image is too large (max {MAX_LOGO_BYTES // (1024 * 1024)}MB).",
                    )
                f.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise

    school = _get_or_create(db)
    school.logo_path = str(dest)
    db.commit()
    return school


@router.get("/logo")
def get_logo(db: Session = Depends(get_db)):
    school = _get_or_create(db)
    if not school.logo_path or not Path(school.logo_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No logo uploaded")
    return FileResponse(school.logo_path)
