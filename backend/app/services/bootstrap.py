from pathlib import Path

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import inspect, select, text

from app.db.session import SessionLocal, engine
from app.logging_config import logger
from app.models.role import Role
from app.models.school import School
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.logo_store import mime_for_filename

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # .../backend


def run_migrations(database_url: str | None = None) -> None:
    """Applies any pending Alembic migrations at startup — to the default
    database, or to the given tenant database URL.

    The Render service deploys with just `pip install` + `uvicorn` — its
    build command does not run `alembic upgrade head`, which made a deploy
    that added columns crash on boot (UndefinedColumn). Running migrations
    here makes every deploy self-contained regardless of how the service is
    configured. Safe with this app's single instance (WEB_CONCURRENCY=1);
    a no-op when the database is already at head.

    The Config is built programmatically without alembic.ini so env.py
    skips fileConfig(), which would otherwise disable the app's own loggers."""
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    if database_url:
        cfg.attributes["db_url"] = database_url
    try:
        alembic_command.upgrade(cfg, "head")
    except Exception as exc:
        raise RuntimeError(
            f"Database migration failed at startup: {exc}. The service will "
            "not start with an out-of-date schema — check DATABASE_URL and "
            "the migration logs above."
        ) from exc


DEFAULT_SCHOOL_NAME = "Bright Future High School"
DEFAULT_CAMPUS_NAME = "Haider Campus"
SUPER_ADMIN_USERNAME = "superadmin"
SUPER_ADMIN_PASSWORD = "Admin@123"


def init_master() -> None:
    """Boots the multi-tenant control plane, self-provisioning everything:

    1. Creates the master database itself if missing.
    2. Creates/updates the master schema (schools, master_users, directory).
    3. Seeds the global super admin on first boot.
    4. Registers the original DATABASE_URL database as the first school, so
       an existing single-school deployment converts in place with all its
       data intact and zero manual steps.
    5. Loads the school registry and migrates every active school database.
    """
    from app.config import settings
    from app.db.master import (
        MasterSessionLocal,
        MasterUser,
        School as MasterSchool,
        ensure_master_database_exists,
        init_master_schema,
    )
    from app.db.tenants import refresh_registry_from_master, registered_school_ids, school_info, tenant_url

    ensure_master_database_exists()
    init_master_schema()

    mdb = MasterSessionLocal()
    try:
        if mdb.execute(select(MasterUser).limit(1)).scalar_one_or_none() is None:
            mdb.add(
                MasterUser(
                    username=SUPER_ADMIN_USERNAME,
                    name="Super Administrator",
                    password_hash=hash_password(SUPER_ADMIN_PASSWORD),
                    role="SuperAdmin",
                    is_active=True,
                )
            )
            mdb.commit()
            logger.warning(
                "Created global super admin (username=%s). Change this password immediately.",
                SUPER_ADMIN_USERNAME,
            )

        if mdb.execute(select(MasterSchool).limit(1)).scalar_one_or_none() is None:
            mdb.add(
                MasterSchool(
                    school_name=DEFAULT_SCHOOL_NAME,
                    campus_name=DEFAULT_CAMPUS_NAME,
                    database_name=settings.default_tenant_dbname,
                    database_status="active",
                )
            )
            mdb.commit()
            logger.info(
                "Registered existing database %r as the first school (%s — %s)",
                settings.default_tenant_dbname, DEFAULT_SCHOOL_NAME, DEFAULT_CAMPUS_NAME,
            )
    finally:
        mdb.close()

    refresh_registry_from_master()

    logger.info("Applying database migrations to all active schools...")
    for school_id in registered_school_ids():
        info = school_info(school_id)
        if info and info["status"] == "active":
            run_migrations(tenant_url(school_id))
    logger.info("All school databases migrated")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

REQUIRED_TABLE = "user_account"

DEFAULT_LOGO_SRC = Path(__file__).resolve().parent.parent / "assets" / "default_school_logo.png"


def verify_database_ready() -> None:
    """Runs on every startup, before anything else touches the database.
    Confirms the configured DATABASE_URL (Neon) is actually reachable and
    that migrations have been applied, so a misconfigured deploy fails fast
    with a clear message instead of crashing later on the first request."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(
            f"Could not connect to the database at the configured DATABASE_URL: {exc}"
        ) from exc
    finally:
        db.close()
    logger.info("Connected to Neon")

    tables = inspect(engine).get_table_names()
    if REQUIRED_TABLE not in tables:
        raise RuntimeError(
            f"Database schema is not initialized — the '{REQUIRED_TABLE}' table "
            "is missing. Run 'alembic upgrade head' against this database "
            "before starting the application."
        )
    logger.info("Database Ready")


def ensure_default_admin() -> None:
    """First-boot convenience: if the database has no users at all (a fresh
    Neon database), creates the Admin role and an admin/admin123 account so
    the app is usable without a manual seeding step. No-op the moment any
    user exists, so it never touches or recreates data in a database that
    already has accounts."""
    db = SessionLocal()
    try:
        if db.execute(select(User.user_id).limit(1)).first() is not None:
            return

        admin_role = db.execute(select(Role).where(Role.role_name == "Admin")).scalar_one_or_none()
        if admin_role is None:
            admin_role = Role(role_name="Admin", description="Full system access")
            db.add(admin_role)
            db.flush()

        db.add(
            User(
                username=DEFAULT_ADMIN_USERNAME,
                full_name="Administrator",
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role_id=admin_role.role_id,
                is_active=True,
            )
        )
        db.commit()
        logger.warning(
            "No users found — created default admin account (username=%s, password=%s). "
            "Change this password immediately.",
            DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD,
        )
    finally:
        db.close()


def ensure_default_logo() -> None:
    """Makes sure the school row has logo bytes in the database. Priority:

    1. logo_data already set — no-op, never overwrites an uploaded logo.
    2. A legacy on-disk logo (logo_path from the pre-database era) still
       exists — import it into logo_data so it finally survives restarts.
    3. Otherwise seed the bundled default logo
       (backend/app/assets/default_school_logo.png), so a fresh deployment
       isn't blank.

    The database is the only durable storage on this Render deployment — a
    disk-stored logo is silently wiped on every restart/redeploy, which is
    exactly the bug this replaces."""
    db = SessionLocal()
    try:
        school = db.execute(select(School).limit(1)).scalar_one_or_none()
        if school is not None and school.logo_data is not None:
            return

        if school is None:
            school = School()
            db.add(school)

        legacy = Path(school.logo_path) if school.logo_path else None
        if legacy is not None and legacy.exists():
            school.logo_data = legacy.read_bytes()
            school.logo_mime = mime_for_filename(legacy.name)
            school.logo_path = None
            db.commit()
            logger.info("Imported legacy on-disk school logo into the database.")
            return

        if not DEFAULT_LOGO_SRC.exists():
            return
        school.logo_data = DEFAULT_LOGO_SRC.read_bytes()
        school.logo_mime = "image/png"
        school.logo_path = None
        db.commit()
        logger.info("Seeded default school logo into the database.")
    finally:
        db.close()
