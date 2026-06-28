"""Run once after migrations to seed roles and a bootstrap Admin user.

Usage: python -m scripts.seed
"""
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.role import Role
from app.models.school import School
from app.models.user import User
from app.services.auth_service import hash_password

ROLE_NAMES = ["Admin", "Accountant", "Teacher"]


def main():
    db = SessionLocal()
    try:
        for name in ROLE_NAMES:
            if db.execute(select(Role).where(Role.role_name == name)).scalar_one_or_none() is None:
                db.add(Role(role_name=name))
        db.commit()

        if db.execute(select(School)).scalar_one_or_none() is None:
            db.add(School())
            db.commit()

        admin_role = db.execute(select(Role).where(Role.role_name == "Admin")).scalar_one()
        if db.execute(select(User).where(User.username == "admin")).scalar_one_or_none() is None:
            db.add(
                User(
                    username="admin",
                    full_name="Administrator",
                    password_hash=hash_password("admin123"),
                    role_id=admin_role.role_id,
                )
            )
            db.commit()
            print("Created bootstrap admin user: username='admin' password='admin123' — change this immediately after first login.")
        else:
            print("Admin user already exists, skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
