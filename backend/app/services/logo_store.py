"""Single source of truth for reading the school logo.

The logo is stored as bytes in the school row (the only durable storage on
this Render + Neon deployment — the local filesystem is wiped on every
restart). A legacy on-disk logo_path is honored as a fallback so old local
installs keep working until bootstrap imports the file into the database.
"""
from pathlib import Path

from app.models.school import School

MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def mime_for_filename(filename: str) -> str:
    return MIME_BY_SUFFIX.get(Path(filename).suffix.lower(), "image/png")


def logo_content(school: School) -> tuple[bytes, str] | None:
    """(bytes, mime) of the school logo, or None if there is no logo at all."""
    if school.logo_data:
        return school.logo_data, school.logo_mime or "image/png"
    if school.logo_path:
        path = Path(school.logo_path)
        if path.exists():
            return path.read_bytes(), mime_for_filename(path.name)
    return None
