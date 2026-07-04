from pathlib import Path

from pydantic import Field, field_validator
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

    # --- Parent module / Firebase Cloud Messaging ---
    # Credentials for sending push to the parent Android app. Optional: the
    # parent module works fully without them (login, data, history) — only the
    # push delivery is skipped when unset. Never hardcode secrets; provide via
    # env, or drop the service-account file at backend/firebase/service-account.json
    # (which is git-ignored). Precedence: JSON env > file env > default file.
    firebase_credentials_json: str | None = None
    firebase_credentials_file: str | None = None
    # Parent app JWT lifetime — parents stay signed in far longer than staff.
    parent_jwt_expire_minutes: int = 60 * 24 * 30  # 30 days

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

    # ------------------------------------------------------------ tenancy
    # DATABASE_URL keeps pointing at the original (first) school database, so
    # an existing single-school deployment converts to multi-tenant with no
    # environment changes. The master database defaults to a sibling database
    # named 'sms_master' on the same PostgreSQL host, overridable via
    # MASTER_DATABASE_URL.
    master_database_url_override: str | None = Field(default=None, alias="master_database_url")

    @property
    def default_tenant_dbname(self) -> str:
        from sqlalchemy.engine.url import make_url
        return make_url(self.database_url).database

    @property
    def master_database_url(self) -> str:
        if self.master_database_url_override:
            v = self.master_database_url_override
            if v.startswith("postgres://"):
                v = "postgresql+psycopg://" + v[len("postgres://"):]
            elif v.startswith("postgresql://"):
                v = "postgresql+psycopg://" + v[len("postgresql://"):]
            return v
        from sqlalchemy.engine.url import make_url
        # render_as_string(hide_password=False): plain str(URL) masks the
        # password as '***', which would silently break authentication.
        return make_url(self.database_url).set(database="sms_master").render_as_string(hide_password=False)

    @property
    def admin_database_url(self) -> str:
        """Connection for server-level admin work (CREATE DATABASE). Uses the
        direct (non-pooled) endpoint: PgBouncer's transaction pooling on
        Neon's '-pooler' hosts can't run CREATE DATABASE."""
        from sqlalchemy.engine.url import make_url
        url = make_url(self.database_url)
        host = (url.host or "").replace("-pooler", "")
        return url.set(host=host).render_as_string(hide_password=False)

    def tenant_database_url(
        self,
        database_name: str,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> str:
        """URL for one school's database — same host/credentials as the base
        deployment unless the school row carries explicit overrides."""
        from sqlalchemy.engine.url import make_url
        url = make_url(self.database_url).set(database=database_name)
        if host:
            url = url.set(host=host)
        if port:
            url = url.set(port=port)
        if username:
            url = url.set(username=username)
        if password:
            url = url.set(password=password)
        return url.render_as_string(hide_password=False)


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
