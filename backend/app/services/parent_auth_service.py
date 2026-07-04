"""JWT + password helpers for parent accounts.

Parent tokens are distinct from staff tokens: they carry ``"type": "parent"``
and ``sub`` = parent_id, so a parent token can never be accepted by the staff
``get_current_user`` dependency (which loads from user_account) and vice-versa.

Critically the parent token ALSO carries the signed ``school_id`` claim, exactly
like staff tokens — that claim is what ``db.session.get_db`` uses to route every
request to the correct tenant (school) database, so the whole multi-tenant
isolation model applies to parents unchanged.
"""
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings
from app.services.auth_service import hash_password, verify_password  # re-exported

__all__ = [
    "hash_password",
    "verify_password",
    "create_parent_access_token",
    "decode_parent_access_token",
]

_PARENT_TOKEN_TYPE = "parent"


def create_parent_access_token(*, parent_id: int, mobile_number: str, school_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.parent_jwt_expire_minutes)
    payload = {
        "sub": str(parent_id),
        "type": _PARENT_TOKEN_TYPE,
        "mobile": mobile_number,
        # Signed school routing claim — read by get_db to pin this session to
        # exactly one tenant database. Clients cannot choose a school any other
        # way, so cross-tenant access is impossible without the signing key.
        "school_id": school_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_parent_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != _PARENT_TOKEN_TYPE:
        raise ValueError("Not a parent token")
    return payload
