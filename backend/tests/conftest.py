"""Smoke-test fixtures.

These tests run against the configured database (the same one the app uses).
To stay isolated and self-cleaning they create their own throwaway role-users,
a throwaway class, and throwaway students — all prefixed/namespaced — and
delete everything in teardown. They never touch the bootstrap admin or real
data.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.main import app
from app.models.attendance import AttendanceRecord
from app.models.communication_provider import CommunicationProvider
from app.models.fee_voucher import FeeVoucher
from app.models.grade import Grade
from app.models.notification_log import NotificationLog
from app.models.notification_queue import NotificationQueue
from app.models.role import Role
from app.models.student import Student
from app.models.user import User
from app.services.auth_service import hash_password

TEST_CLASS = "ZZ Smoke Class"
TEST_PASSWORD = "smoke_pass_123"
TEST_USERNAMES = {"Admin": "smoke_admin", "Accountant": "smoke_acct", "Teacher": "smoke_teacher"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def _seed_test_principals():
    """Creates the throwaway class + one user per role, tears them down after."""
    db = SessionLocal()
    created_user_ids = []
    try:
        if db.execute(select(Grade).where(Grade.class_name == TEST_CLASS)).scalar_one_or_none() is None:
            db.add(Grade(class_name=TEST_CLASS, fee_amount=1000))
            db.commit()

        for role_name, username in TEST_USERNAMES.items():
            role = db.execute(select(Role).where(Role.role_name == role_name)).scalar_one_or_none()
            if role is None:
                role = Role(role_name=role_name)
                db.add(role)
                db.commit()
            existing = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
            if existing:
                # Clear any notifications this user queued in a prior run first,
                # else the FK on notification_queue.created_by blocks the delete.
                db.execute(delete(NotificationQueue).where(NotificationQueue.created_by == existing.user_id))
                db.delete(existing)
                db.commit()
            user = User(
                username=username,
                full_name=f"Smoke {role_name}",
                password_hash=hash_password(TEST_PASSWORD),
                role_id=role.role_id,
                assigned_class_name=TEST_CLASS if role_name == "Teacher" else None,
            )
            db.add(user)
            db.commit()
            created_user_ids.append(user.user_id)
        yield
    finally:
        # Clean up any students left in the test class plus their dependents,
        # and any notifications queued by the throwaway users (these may have
        # had their student_id nulled out when the student was deleted).
        if created_user_ids:
            db.execute(delete(NotificationQueue).where(NotificationQueue.created_by.in_(created_user_ids)))
        student_ids = db.execute(
            select(Student.student_id).where(Student.class_name == TEST_CLASS)
        ).scalars().all()
        if student_ids:
            db.execute(delete(NotificationQueue).where(NotificationQueue.student_id.in_(student_ids)))
            db.execute(delete(AttendanceRecord).where(AttendanceRecord.student_id.in_(student_ids)))
            db.execute(delete(FeeVoucher).where(FeeVoucher.student_id.in_(student_ids)))
            db.execute(delete(Student).where(Student.student_id.in_(student_ids)))
        db.execute(delete(User).where(User.user_id.in_(created_user_ids)))
        db.execute(delete(Grade).where(Grade.class_name == TEST_CLASS))
        # WhatsApp "Send Test Message" diagnostic logs (student_id is always
        # NULL for these — they're not tied to a student) — wipe them so
        # repeated test runs don't pollute the real Communication History.
        db.execute(delete(NotificationLog).where(NotificationLog.notification_type == "test"))
        db.execute(delete(CommunicationProvider).where(CommunicationProvider.name.like("Smoke WA Account%")))
        db.commit()
        db.close()


def _token(client: TestClient, username: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(client):
    return {"Authorization": f"Bearer {_token(client, TEST_USERNAMES['Admin'])}"}


@pytest.fixture(scope="session")
def accountant_headers(client):
    return {"Authorization": f"Bearer {_token(client, TEST_USERNAMES['Accountant'])}"}


@pytest.fixture(scope="session")
def teacher_headers(client):
    return {"Authorization": f"Bearer {_token(client, TEST_USERNAMES['Teacher'])}"}


@pytest.fixture
def temp_student(client, admin_headers):
    """Creates a student in the test class and deletes it (and dependents) after."""
    resp = client.post(
        "/api/students",
        headers=admin_headers,
        json={"name": "Smoke Student", "father_name": "Smoke Parent", "class_name": TEST_CLASS,
              "phone": "03001112222", "default_fee": 1000},
    )
    assert resp.status_code == 200, resp.text
    student = resp.json()
    yield student
    client.delete(f"/api/students/{student['student_id']}", headers=admin_headers)
