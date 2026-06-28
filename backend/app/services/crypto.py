"""Symmetric encryption for credentials stored in the database (e.g. WhatsApp
Business access tokens). Never used for anything else — passwords still go
through bcrypt, JWTs still go through python-jose.

Requires `CREDENTIALS_ENCRYPTION_KEY` in the environment (a Fernet key,
generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
"""
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class EncryptionKeyMissing(Exception):
    """Raised when CREDENTIALS_ENCRYPTION_KEY is not set."""


def _fernet() -> Fernet:
    if not settings.credentials_encryption_key:
        raise EncryptionKeyMissing("CREDENTIALS_ENCRYPTION_KEY is not set in the environment.")
    return Fernet(settings.credentials_encryption_key.encode())


def encrypt(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored credential could not be decrypted — the encryption key may have changed.") from exc
