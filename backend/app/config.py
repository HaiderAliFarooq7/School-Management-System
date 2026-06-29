import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sms_user:sms_pass@localhost:5432/sms_db"
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours
    pg_bin_dir: str = ""  # e.g. "C:\\Program Files\\PostgreSQL\\18\\bin" — empty means rely on PATH

    data_dir: Path = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SMS"

    # Comma-separated list of allowed browser origins for CORS, needed when the
    # frontend is hosted separately from the backend (e.g. Vercel + Render).
    # When the frontend is instead served by this same app (StaticFiles mount
    # below), the browser never makes a cross-origin request and this is moot.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _force_psycopg3_driver(cls, v: str) -> str:
        """Hosting providers (Render, Neon, Heroku-style URLs) hand out bare
        ``postgresql://`` or legacy ``postgres://`` connection strings with no
        driver suffix. SQLAlchemy's default dialect for both of those schemes
        is psycopg2, which this project does not install (psycopg v3 only,
        via ``psycopg[binary]``) — causing ``ModuleNotFoundError: No module
        named 'psycopg2'`` at engine-connect time. Normalize to the psycopg
        v3 driver here so every consumer (the app engine, Alembic) gets a
        working URL no matter what the platform's env var looks like."""
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

# Only persistent assets live on disk: the school logo and student photos.
# Backups, generated PDFs, QR images, and Excel exports are produced on
# demand, streamed to the client, and never retained on the server — this
# keeps the app friendly to free/ephemeral hosting with no durable disk.
PHOTOS_DIR = settings.data_dir / "photos"
LOGO_DIR = settings.data_dir / "logo"

LOG_DIR = settings.data_dir / "logs"

for d in (PHOTOS_DIR, LOGO_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)
