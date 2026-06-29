import shutil
from pathlib import Path

from sqlalchemy import inspect, select, text

from app.config import LOGO_DIR
from app.db.session import SessionLocal, engine
from app.logging_config import logger
from app.models.role import Role
from app.models.school import School
from app.models.user import User
from app.services.auth_service import hash_password

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
    """First-boot convenience: if the school record has no logo yet, seeds it
    with the bundled default logo (backend/app/assets/default_school_logo.png)
    so a fresh deployment isn't blank. No-op the instant any logo_path is
    already set, so it never overwrites an admin's own uploaded logo."""
    if not DEFAULT_LOGO_SRC.exists():
        return

    db = SessionLocal()
    try:
        school = db.execute(select(School).limit(1)).scalar_one_or_none()
        if school is not None and school.logo_path:
            return

        dest = LOGO_DIR / "school_logo.png"
        shutil.copyfile(DEFAULT_LOGO_SRC, dest)

        if school is None:
            school = School()
            db.add(school)
        school.logo_path = str(dest)
        db.commit()
        logger.info("Seeded default school logo.")
    finally:
        db.close()
