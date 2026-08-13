"""Resets the global SuperAdmin account (master DB) to a known username/password.

Creates the account if it doesn't exist yet, otherwise updates it in place.

Usage (run where MASTER_DATABASE_URL / DATABASE_URL is already configured,
e.g. the Render Shell for the backend service):

    python -m scripts.reset_superadmin
"""
from sqlalchemy import select

from app.db.master import MasterSessionLocal, MasterUser
from app.services.auth_service import hash_password

USERNAME = "superadmin"
PASSWORD = "alihaiderA11.."


def main():
    db = MasterSessionLocal()
    try:
        user = db.execute(select(MasterUser).where(MasterUser.username == USERNAME)).scalar_one_or_none()
        if user is None:
            db.add(
                MasterUser(
                    username=USERNAME,
                    name="Super Administrator",
                    password_hash=hash_password(PASSWORD),
                    role="SuperAdmin",
                    is_active=True,
                )
            )
            print(f"Created SuperAdmin account: username='{USERNAME}'.")
        else:
            user.password_hash = hash_password(PASSWORD)
            user.is_active = True
            print(f"Reset password for existing SuperAdmin account: username='{USERNAME}'.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
