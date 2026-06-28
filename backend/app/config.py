import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sms_user:sms_pass@localhost:5432/sms_db"
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours
    pg_bin_dir: str = ""  # e.g. "C:\\Program Files\\PostgreSQL\\18\\bin" — empty means rely on PATH

    data_dir: Path = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SMS"

    # Symmetric key for encrypting credentials stored in the DB (e.g. WhatsApp
    # Business access tokens). Generate with:
    # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    credentials_encryption_key: str = ""

    # Comma-separated list of allowed browser origins for CORS, needed when the
    # frontend is hosted separately from the backend (e.g. Vercel + Render).
    # When the frontend is instead served by this same app (StaticFiles mount
    # below), the browser never makes a cross-origin request and this is moot.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
