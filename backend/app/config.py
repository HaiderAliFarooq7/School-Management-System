from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production-only configuration. Every value below is read from the
    Render service's environment variables — there is no local/dev fallback
    for the database or CORS origins; missing either one fails startup
    immediately with a clear error rather than silently degrading."""

    database_url: str | None = None
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours
    pg_bin_dir: str = ""  # only needed if pg_dump/pg_restore aren't already on PATH

    # Defaults to a guaranteed-writable ephemeral path. If a Render
    # persistent disk is attached (mounted at /var/data by convention), set
    # DATA_DIR=/var/data/sms so the school logo and student photos survive
    # restarts/deploys; otherwise they're lost on every restart like the
    # rest of this app's on-disk state.
    data_dir: Path = Path("/tmp/sms")

    # Comma-separated list of allowed browser origins for CORS — the Vercel
    # production frontend domain, plus an optional custom domain. Required;
    # there is no localhost default since this app never runs locally.
    cors_origins: str | None = None

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _require_and_normalize_database_url(cls, v: str | None) -> str:
        """Render/Neon hand out bare ``postgresql://`` or legacy
        ``postgres://`` connection strings with no driver suffix.
        SQLAlchemy's default dialect for both schemes is psycopg2, which this
        project does not install (psycopg v3 only, via ``psycopg[binary]``) —
        causing ``ModuleNotFoundError: No module named 'psycopg2'`` at
        engine-connect time. Normalize to the psycopg v3 driver here so every
        consumer (the app engine, Alembic) gets a working URL. A missing
        value fails fast: this app only ever talks to Neon in production,
        there is no local-database fallback."""
        if not v:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. Set it in the "
                "Render dashboard to your Neon PostgreSQL connection string "
                "before starting this application."
            )
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @field_validator("cors_origins")
    @classmethod
    def _require_cors_origins(cls, v: str | None) -> str:
        if not v:
            raise RuntimeError(
                "CORS_ORIGINS environment variable is not set. Set it in the "
                "Render dashboard to your Vercel production frontend domain "
                "(plus any custom domain), comma-separated — e.g. "
                "https://your-app.vercel.app,https://your-custom-domain.com"
            )
        return v

    # Optional explicit public URL of the frontend (no trailing slash) used
    # for links embedded in printed material (the fee-challan QR code).
    # Defaults to the first CORS origin, which is already required to be the
    # production frontend domain.
    public_app_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def app_base_url(self) -> str:
        return (self.public_app_url or self.cors_origin_list[0]).rstrip("/")


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
