"""Per-tenant engine registry.

One SQLAlchemy engine (with its own connection pool) per school database,
created lazily on first use and cached for the process lifetime. Small pools
per tenant keep total connections well inside Neon's limits while still
giving every school pooled, pre-pinged connections.
"""
import threading

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_lock = threading.Lock()
_engines: dict[str, Engine] = {}
_sessionmakers: dict[str, sessionmaker] = {}

# school_id -> connection info, loaded from the master DB at startup and
# refreshed whenever schools change. Kept as a plain dict so request handling
# never needs a master-DB query on the hot path.
_school_registry: dict[int, dict] = {}
_default_school_id: int | None = None


def register_school(
    school_id: int,
    database_name: str,
    status: str = "active",
    host: str | None = None,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    school_name: str = "",
    campus_name: str = "",
) -> None:
    _school_registry[school_id] = {
        "database_name": database_name,
        "status": status,
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "school_name": school_name,
        "campus_name": campus_name,
    }


def set_default_school(school_id: int) -> None:
    global _default_school_id
    _default_school_id = school_id


def default_school_id() -> int | None:
    return _default_school_id


def school_info(school_id: int) -> dict | None:
    return _school_registry.get(school_id)


def registered_school_ids() -> list[int]:
    return list(_school_registry)


def tenant_url(school_id: int) -> str:
    info = _school_registry.get(school_id)
    if info is None:
        raise KeyError(f"Unknown school_id {school_id}")
    return settings.tenant_database_url(
        info["database_name"], info["host"], info["port"], info["username"], info["password"]
    )


def tenant_engine(school_id: int) -> Engine:
    url = tenant_url(school_id)
    with _lock:
        engine = _engines.get(url)
        if engine is None:
            engine = create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=5)
            _engines[url] = engine
            _sessionmakers[url] = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return engine


def tenant_session(school_id: int) -> Session:
    url = tenant_url(school_id)
    with _lock:
        maker = _sessionmakers.get(url)
    if maker is None:
        tenant_engine(school_id)
        with _lock:
            maker = _sessionmakers[url]
    return maker()


def dispose_engine_for(school_id: int) -> None:
    """Drops the cached engine (e.g. before a restore or after archiving)."""
    try:
        url = tenant_url(school_id)
    except KeyError:
        return
    with _lock:
        engine = _engines.pop(url, None)
        _sessionmakers.pop(url, None)
    if engine is not None:
        engine.dispose()


def refresh_registry_from_master() -> None:
    """Reloads the school registry from the master database. Called at
    startup and after any school create/update in the master API."""
    from sqlalchemy import select
    from app.db.master import MasterSessionLocal, School

    db = MasterSessionLocal()
    try:
        schools = db.execute(select(School)).scalars().all()
        _school_registry.clear()
        first_active: int | None = None
        for s in schools:
            register_school(
                s.school_id, s.database_name, s.database_status,
                s.database_host, s.database_port, s.database_username, s.database_password,
                s.school_name, s.campus_name,
            )
            if first_active is None and s.database_status == "active":
                first_active = s.school_id
            # The school running on the original DATABASE_URL database is the
            # fallback tenant for logins not present in the user directory.
            if s.database_name == settings.default_tenant_dbname:
                set_default_school(s.school_id)
        if _default_school_id is None and first_active is not None:
            set_default_school(first_active)
    finally:
        db.close()
