"""School provisioning: everything that happens when the super admin clicks
'Create School'.

    1. CREATE DATABASE on the PostgreSQL server (direct/non-pooled endpoint —
       PgBouncer can't run CREATE DATABASE).
    2. Run the full Alembic migration chain against the new database.
    3. Seed the default roles and the school's Admin account.
    4. Register the school + admin routing in the master database.

Deleting a school never drops the physical database — it archives the row,
which blocks logins and hides the school, while the data stays recoverable.
"""
import re

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.master import School, UserDirectory
from app.db.tenants import refresh_registry_from_master
from app.logging_config import logger
from app.models.role import Role
from app.models.school import School as TenantSchoolProfile
from app.models.user import User
from app.services.auth_service import hash_password

DBNAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,62}$")
DEFAULT_ROLES = [
    ("Admin", "Full school access"),
    ("Accountant", "Fee collection and student records"),
    ("Teacher", "Attendance for the assigned class"),
]


def validate_database_name(name: str) -> str:
    """Only lowercase letters/digits/underscores — the name is interpolated
    into CREATE DATABASE, so the strict allow-list is the injection guard."""
    name = name.strip().lower()
    if not DBNAME_RE.match(name):
        raise ValueError(
            "Database name must start with a letter and contain only lowercase "
            "letters, digits, and underscores (3-63 characters)."
        )
    return name


def create_physical_database(database_name: str) -> bool:
    """Creates the database on the server if missing. Returns True if created."""
    database_name = validate_database_name(database_name)
    admin_engine = create_engine(
        settings.admin_database_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": database_name}
            ).first()
            if exists:
                return False
            logger.info("Creating tenant database %s", database_name)
            conn.execute(text(f'CREATE DATABASE "{database_name}"'))
            return True
    finally:
        admin_engine.dispose()


def migrate_database(database_url: str) -> None:
    """Applies the full existing Alembic chain to one tenant database."""
    from pathlib import Path
    from alembic import command as alembic_command
    from alembic.config import Config as AlembicConfig

    backend_dir = Path(__file__).resolve().parent.parent.parent
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    cfg.attributes["db_url"] = database_url
    alembic_command.upgrade(cfg, "head")


def seed_school_database(
    database_url: str,
    school_name: str,
    campus_name: str,
    admin_username: str,
    admin_password: str,
    admin_full_name: str = "School Administrator",
) -> None:
    """Roles + school profile + Admin account inside a fresh tenant database.
    Idempotent — safe to re-run if provisioning is retried."""
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionMaker = sessionmaker(bind=engine)
    db: Session = SessionMaker()
    try:
        roles: dict[str, Role] = {}
        for role_name, description in DEFAULT_ROLES:
            role = db.execute(select(Role).where(Role.role_name == role_name)).scalar_one_or_none()
            if role is None:
                role = Role(role_name=role_name, description=description)
                db.add(role)
                db.flush()
            roles[role_name] = role

        profile = db.execute(select(TenantSchoolProfile).limit(1)).scalar_one_or_none()
        if profile is None:
            profile = TenantSchoolProfile()
            db.add(profile)
        display = f"{school_name} — {campus_name}" if campus_name else school_name
        if not profile.name:
            profile.name = display

        if db.execute(select(User).where(User.username == admin_username)).scalar_one_or_none() is None:
            db.add(
                User(
                    username=admin_username,
                    full_name=admin_full_name,
                    password_hash=hash_password(admin_password),
                    role_id=roles["Admin"].role_id,
                    is_active=True,
                )
            )
        db.commit()
    finally:
        db.close()
        engine.dispose()


def provision_school(
    mdb: Session,
    *,
    school_name: str,
    campus_name: str,
    database_name: str,
    admin_username: str,
    admin_password: str,
) -> School:
    """Full create-school flow. `mdb` is a master-database session."""
    database_name = validate_database_name(database_name)
    admin_username = admin_username.strip()
    if len(admin_password) < 8:
        raise ValueError("Admin password must be at least 8 characters.")
    if not admin_username:
        raise ValueError("Admin username is required.")

    if mdb.execute(select(School).where(School.database_name == database_name)).scalar_one_or_none():
        raise ValueError(f"A school already uses the database name '{database_name}'.")
    existing_route = mdb.execute(
        select(UserDirectory).where(UserDirectory.username == admin_username)
    ).scalar_one_or_none()
    if existing_route is not None:
        raise ValueError(f"Username '{admin_username}' is already used by another school.")

    create_physical_database(database_name)
    url = settings.tenant_database_url(database_name)
    migrate_database(url)
    seed_school_database(url, school_name, campus_name, admin_username, admin_password)

    school = School(
        school_name=school_name.strip(),
        campus_name=campus_name.strip(),
        database_name=database_name,
        database_status="active",
    )
    mdb.add(school)
    mdb.flush()
    mdb.add(UserDirectory(username=admin_username, school_id=school.school_id))
    mdb.commit()

    refresh_registry_from_master()
    logger.info(
        "Provisioned school %s (%s) on database %s with admin %r",
        school.school_name, school.campus_name, database_name, admin_username,
    )
    return school
