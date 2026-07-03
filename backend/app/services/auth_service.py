from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(
    *,
    user_id: int,
    role_name: str,
    assigned_class_name: str | None,
    school_id: int | None = None,
    is_super: bool = False,
) -> str:
    """The signed school_id claim is what pins every request of this session
    to exactly one tenant database — clients cannot choose a school any
    other way, so cross-tenant access is impossible without the signing key."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role_name,
        "assigned_class_name": assigned_class_name,
        "school_id": school_id,
        "is_super": is_super,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
