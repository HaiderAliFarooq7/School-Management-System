"""Parent-module tests: parent login by mobile number, one parent seeing
multiple children, read-only data endpoints, tenant isolation of parent tokens,
and the notification-center role rules (Admin any / Accountant fee-only /
Teacher forbidden).

Like the other tests these run against the configured (default-school) database
and clean up after themselves. Firebase is not configured in tests, so pushes
are simply skipped — the in-app notification rows and audit log are still
written and asserted.
"""
import pytest
from sqlalchemy import delete, select

from conftest import TEST_CLASS, TEST_PASSWORD, TEST_USERNAMES
from app.db.master import MasterSessionLocal, ParentDirectory
from app.db.session import SessionLocal
from app.models.notification_log import NotificationLog
from app.models.parent_account import ParentAccount
from app.models.parent_notification import ParentNotification
from app.services.parent_linking import normalize_mobile

PARENT_MOBILE = "03007654321"


@pytest.fixture
def parent_with_children(client, admin_headers):
    """Two students in the test class sharing one mobile number, plus the
    parent account (created via the admin API, default password = mobile).
    Cleans up students, the parent account, its notifications, and the master
    directory row afterwards."""
    student_ids = []
    for name in ("Parent Child One", "Parent Child Two"):
        resp = client.post(
            "/api/students",
            headers=admin_headers,
            json={"name": name, "father_name": "Test Parent", "class_name": TEST_CLASS,
                  "phone": PARENT_MOBILE, "default_fee": 1000},
        )
        assert resp.status_code == 200, resp.text
        student_ids.append(resp.json()["student_id"])

    created = client.post(
        "/api/admin/parents",
        headers=admin_headers,
        json={"mobile_number": PARENT_MOBILE, "full_name": "Test Parent"},
    )
    assert created.status_code == 200, created.text
    parent_id = created.json()["parent_id"]

    yield {"student_ids": student_ids, "parent_id": parent_id, "mobile": PARENT_MOBILE}

    for sid in student_ids:
        client.delete(f"/api/students/{sid}", headers=admin_headers)
    db = SessionLocal()
    try:
        db.execute(delete(ParentNotification).where(ParentNotification.parent_id == parent_id))
        db.execute(delete(ParentAccount).where(ParentAccount.parent_id == parent_id))
        db.commit()
    finally:
        db.close()
    mdb = MasterSessionLocal()
    try:
        mdb.execute(
            delete(ParentDirectory).where(ParentDirectory.mobile_core == normalize_mobile(PARENT_MOBILE))
        )
        mdb.commit()
    finally:
        mdb.close()


def _parent_token(client, mobile: str, password: str) -> str:
    resp = client.post("/api/parent/login", json={"mobile_number": mobile, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_parent_login_default_password_is_mobile(client, parent_with_children):
    resp = client.post(
        "/api/parent/login",
        json={"mobile_number": PARENT_MOBILE, "password": PARENT_MOBILE},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["must_change_password"] is True


def test_parent_login_wrong_password_rejected(client, parent_with_children):
    resp = client.post(
        "/api/parent/login",
        json={"mobile_number": PARENT_MOBILE, "password": "not-the-password"},
    )
    assert resp.status_code == 401


def test_parent_sees_all_their_children(client, parent_with_children):
    token = _parent_token(client, PARENT_MOBILE, PARENT_MOBILE)
    resp = client.get("/api/parent/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    returned = {int(s["id"]) for s in resp.json()}
    assert set(parent_with_children["student_ids"]).issubset(returned)


def test_parent_read_endpoints(client, parent_with_children):
    token = _parent_token(client, PARENT_MOBILE, PARENT_MOBILE)
    headers = {"Authorization": f"Bearer {token}"}
    sid = parent_with_children["student_ids"][0]
    assert client.get(f"/api/parent/students/{sid}/attendance", headers=headers).status_code == 200
    assert client.get(f"/api/parent/students/{sid}/fees", headers=headers).status_code == 200
    assert client.get(f"/api/parent/students/{sid}/extra-charges", headers=headers).status_code == 200
    assert client.get("/api/parent/notifications", headers=headers).status_code == 200
    assert client.get("/api/parent/school", headers=headers).status_code == 200


def test_parent_cannot_read_other_students(client, parent_with_children, admin_headers):
    """A parent asking for a student that isn't theirs gets 404, not another
    family's data."""
    other = client.post(
        "/api/students", headers=admin_headers,
        json={"name": "Unrelated Child", "father_name": "Someone Else", "class_name": TEST_CLASS,
              "phone": "03009998888", "default_fee": 1000},
    )
    other_id = other.json()["student_id"]
    try:
        token = _parent_token(client, PARENT_MOBILE, PARENT_MOBILE)
        resp = client.get(
            f"/api/parent/students/{other_id}/attendance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
    finally:
        client.delete(f"/api/students/{other_id}", headers=admin_headers)


def test_staff_token_rejected_on_parent_api(client, admin_headers):
    """A staff JWT must not be accepted by parent endpoints."""
    assert client.get("/api/parent/students", headers=admin_headers).status_code == 401


def test_parent_token_rejected_on_staff_api(client, parent_with_children):
    token = _parent_token(client, PARENT_MOBILE, PARENT_MOBILE)
    resp = client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# --------------------------------------------------------- notification center

def test_teacher_cannot_send_notification(client, teacher_headers):
    resp = client.post(
        "/api/admin/notifications/send", headers=teacher_headers,
        json={"notif_type": "announcement", "audience": "school", "title": "Hi", "body": "Test"},
    )
    assert resp.status_code == 403


def test_accountant_can_only_send_fee_reminders(client, accountant_headers):
    blocked = client.post(
        "/api/admin/notifications/send", headers=accountant_headers,
        json={"notif_type": "announcement", "audience": "school", "title": "Hi", "body": "Test"},
    )
    assert blocked.status_code == 403

    allowed = client.post(
        "/api/admin/notifications/send", headers=accountant_headers,
        json={"notif_type": "fee_reminder", "audience": "school", "title": "Fees due", "body": "Please pay."},
    )
    assert allowed.status_code == 200, allowed.text
    _cleanup_log(allowed.json()["log_id"])


def test_admin_announcement_reaches_parent_inbox(client, admin_headers, parent_with_children):
    sent = client.post(
        "/api/admin/notifications/send", headers=admin_headers,
        json={"notif_type": "announcement", "audience": "school",
              "title": "School reopens Monday", "body": "Welcome back."},
    )
    assert sent.status_code == 200, sent.text
    log_id = sent.json()["log_id"]

    token = _parent_token(client, PARENT_MOBILE, PARENT_MOBILE)
    inbox = client.get("/api/parent/notifications", headers={"Authorization": f"Bearer {token}"})
    assert inbox.status_code == 200
    assert any(n["title"] == "School reopens Monday" for n in inbox.json())
    _cleanup_log(log_id)


def test_class_fee_reminder_is_personalized(client, admin_headers, parent_with_children):
    """A class/school fee reminder with short-codes must reach each parent with
    their own child's real name/class/amount filled in — not literal
    '{amount} ... {student}' placeholders."""
    sent = client.post(
        "/api/admin/notifications/send", headers=admin_headers,
        json={
            "notif_type": "fee_reminder", "audience": "class", "class_name": TEST_CLASS,
            "title": "Fee Reminder",
            "body": "Dear Parent, {amount} is pending for {student} ({class}). Kindly clear the dues.",
        },
    )
    assert sent.status_code == 200, sent.text
    log_id = sent.json()["log_id"]

    token = _parent_token(client, PARENT_MOBILE, PARENT_MOBILE)
    inbox = client.get("/api/parent/notifications", headers={"Authorization": f"Bearer {token}"})
    assert inbox.status_code == 200
    bodies = [n["body"] for n in inbox.json()]
    # A real child's name appears and no short-code braces/brackets remain.
    assert any(
        "Parent Child" in b and "{" not in b and "[" not in b and TEST_CLASS in b
        for b in bodies
    ), bodies
    _cleanup_log(log_id)


def _cleanup_log(log_id: int) -> None:
    db = SessionLocal()
    try:
        db.execute(delete(NotificationLog).where(NotificationLog.log_id == log_id))
        db.commit()
    finally:
        db.close()
