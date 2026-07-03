import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_role
from app.models.school import School
from app.schemas.school import SchoolOut, SchoolUpdate
from app.services.logo_store import logo_content, mime_for_filename

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


@router.get("", response_model=SchoolOut, dependencies=[Depends(get_current_user)])
def get_school(db: Session = Depends(get_db)):
    """Any signed-in user. Only /logo below stays public — it's referenced
    from plain <img src> tags that can't carry an Authorization header."""
    return _get_or_create(db)


@router.put("", response_model=SchoolOut, dependencies=[Depends(require_role("Admin"))])
def update_school(payload: SchoolUpdate, db: Session = Depends(get_db)):
    school = _get_or_create(db)
    for field, value in payload.model_dump().items():
        setattr(school, field, value)
    db.commit()
    return school


@router.post("/logo", response_model=SchoolOut, dependencies=[Depends(require_role("Admin"))])
async def upload_logo(file: UploadFile, db: Session = Depends(get_db)):
    """Stores the logo bytes in the database. Writing it to disk looked like
    it worked but silently lost the file on Render, whose filesystem is wiped
    on every restart/redeploy/idle spin-down — the database is the only
    durable storage in this deployment."""
    suffix = Path(file.filename or "logo.png").suffix.lower() or ".png"
    if suffix not in ALLOWED_LOGO_SUFFIXES or not (file.content_type or "").startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please upload an image file (PNG, JPG, GIF, or WEBP).")

    data = await file.read(MAX_LOGO_BYTES + 1)
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Logo image is too large (max {MAX_LOGO_BYTES // (1024 * 1024)}MB).",
        )

    # These bytes are served back publicly from GET /logo, so make sure they
    # really decode as an image and not something else wearing a .png name.
    try:
        PILImage.open(io.BytesIO(data)).verify()
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This file doesn't appear to be a valid image.")

    school = _get_or_create(db)
    school.logo_data = data
    school.logo_mime = mime_for_filename(f"logo{suffix}")
    school.logo_path = None  # the DB copy supersedes any legacy disk file
    db.commit()
    return school


@router.get("/logo")
def get_logo(db: Session = Depends(get_db)):
    """Public (used from plain <img src>). no-cache makes the browser
    revalidate after a new upload while still allowing conditional reuse."""
    school = _get_or_create(db)
    content = logo_content(school)
    if content is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No logo uploaded")
    data, mime = content
    return Response(content=data, media_type=mime, headers={"Cache-Control": "no-cache"})
