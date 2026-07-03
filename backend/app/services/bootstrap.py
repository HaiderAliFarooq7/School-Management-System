from pathlib import Path

from sqlalchemy import inspect, select, text

from app.db.session import SessionLocal, engine
from app.logging_config import logger
from app.models.role import Role
from app.models.school import School
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.logo_store import mime_for_filename

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
