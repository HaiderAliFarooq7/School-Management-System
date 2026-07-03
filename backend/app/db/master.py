"""Master (control-plane) database: the one place that knows every school.

The master database stores ONLY routing and control data:
  - schools            — one row per tenant school + its database location
  - master_users       — global users (the super admin); never tenant staff
  - user_directory     — username -> school routing for login (tenant users
                         stay authoritative inside their own school database,
                         so change-password / user management keep working
                         exactly as before)

Every school's operational data lives in its own PostgreSQL database with
the existing schema. Nothing in a tenant database can reference another
tenant — isolation is physical, not just logical.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, create_engine, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import settings
from app.logging_config import logger


class MasterBase(DeclarativeBase):
    pass


class School(MasterBase):
    __tablename__ = "schools"

    school_id: Mapped[int] = mapped_column(primary_key=True)
    school_name: Mapped[str] = mapped_column(String(255), nullable=False)
    campus_name: Mapped[str] = mapped_column(String(255), default="")
    database_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    # Optional per-school connection overrides. Normally NULL — the school
    # database lives on the same PostgreSQL host as the master, and the
    # base credentials from MASTER_DATABASE_URL/DATABASE_URL are reused.
    database_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    database_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    database_username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    database_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # active | disabled | archived
    database_status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MasterUser(MasterBase):
    """Global (cross-school) accounts — currently just the super admin."""
    __tablename__ = "master_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), default="")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="SuperAdmin", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserDirectory(MasterBase):
    """username -> school routing for login. Passwords are NOT stored here;
    after routing, credentials are verified against the school's own
    user_account table (single source of truth, so self-service password
    changes inside a school require no master sync)."""
    __tablename__ = "user_directory"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    school_id: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------- engine

master_engine = create_engine(settings.master_database_url, pool_pre_ping=True, pool_size=3, max_overflow=5)
MasterSessionLocal = sessionmaker(bind=master_engine, autoflush=False, autocommit=False)


def get_master_db():
    db = MasterSessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_master_database_exists() -> None:
    """Creates the master database itself on first boot (CREATE DATABASE via
    the admin/default connection), so converting an existing single-school
    deployment to multi-tenant needs no manual database work."""
    try:
        with master_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return  # master DB already exists and is reachable
    except Exception:
        pass

    admin_engine = create_engine(settings.admin_database_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    master_dbname = settings.master_database_url.rsplit("/", 1)[1].split("?")[0]
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": master_dbname}
        ).first()
        if not exists:
            logger.info("Creating master database %s", master_dbname)
            conn.execute(text(f'CREATE DATABASE "{master_dbname}"'))
    admin_engine.dispose()


def init_master_schema() -> None:
    """Master schema is small and additive; created/updated via metadata."""
    MasterBase.metadata.create_all(master_engine)
