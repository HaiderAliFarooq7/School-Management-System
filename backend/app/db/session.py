"""Tenant-aware database sessions.

Every existing router depends on `get_db` — it now resolves WHICH school's
database to hand out, per request:

  1. the `school_id` claim inside the request's JWT (normal case), else
  2. an explicit `school_id` query parameter (only used by public,
     token-less endpoints like the school-logo <img>), else
  3. the default school — the database DATABASE_URL points at, which is how
     the original single-school deployment keeps working unchanged.

A request can never reach another school's data by manipulating headers:
the school_id comes from the *signed* JWT, and disabled/archived schools
are refused before a connection is ever handed out.

`engine`/`SessionLocal` remain exported, bound to the default (original)
database — used by bootstrap, scripts, and the smoke-test fixtures.
"""
from fastapi import HTTPException, Request, status
from jose import JWTError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def resolve_school_id(request: Request) -> int:
    from app.db.tenants import default_school_id, school_info
    from app.services.auth_service import decode_access_token

    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            payload = decode_access_token(auth[7:].strip())
            sid = payload.get("school_id")
            if sid is not None:
                sid = int(sid)
                info = school_info(sid)
                if info is None:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, "Unknown school for this session.")
                if info["status"] != "active" and not payload.get("is_super"):
                    raise HTTPException(
                        status.HTTP_403_FORBIDDEN,
                        "This school is currently disabled. Contact the system administrator.",
                    )
                return sid
        except JWTError:
            # Invalid/expired token: fall through — the auth dependency on
            # protected endpoints will return the proper 401.
            pass

    qp = request.query_params.get("school_id")
    if qp and qp.isdigit():
        from app.db.tenants import school_info as _info
        if _info(int(qp)) is not None:
            return int(qp)

    from app.db.tenants import default_school_id as _default
    did = _default()
    if did is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "No schools are registered yet — the system is still initializing.",
        )
    return did


def get_db(request: Request):
    from app.db.tenants import tenant_session

    school_id = resolve_school_id(request)
    db: Session = tenant_session(school_id)
    try:
        yield db
    finally:
        db.close()
