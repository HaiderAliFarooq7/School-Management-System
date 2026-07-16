"""End-to-end smoke tests across the core modules: auth, students, search,
fees, attendance, reports, and role-based permissions. They
assert the happy path works and that role restrictions are actually enforced
by the backend (not just hidden in the UI)."""
from datetime import date

from conftest import TEST_CLASS, TEST_PASSWORD


# ---------------------------------------------------------------- health/auth
def test_ping(client):
    assert client.get("/api/ping").json() == {"status": "ok"}


def test_login_and_me(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers)
    assert me.status_code == 200
    assert me.json()["role"] == "Admin"


def test_bad_login_rejected(client):
    resp = client.post("/api/auth/login", json={"username": "smoke_admin", "password": "wrong"})
    assert resp.status_code == 401


def test_change_password_flow(client, admin_headers):
    # Wrong current password is rejected.
    bad = client.post(
        "/api/auth/change-password", headers=admin_headers,
        json={"current_password": "wrong", "new_password": "newpass123"},
    )
    assert bad.status_code == 400
    # Valid change succeeds, then restore so session login fixtures stay valid.
    ok = client.post(
        "/api/auth/change-password", headers=admin_headers,
        json={"current_password": TEST_PASSWORD, "new_password": "newpass123"},
    )
    assert ok.status_code == 200
    back = client.post(
        "/api/auth/change-password", headers=admin_headers,
        json={"current_password": "newpass123", "new_password": TEST_PASSWORD},
    )
    assert back.status_code == 200


def test_unauthenticated_request_rejected(client):
    assert client.get("/api/students").status_code == 401


# ----------------------------------------------------------------- students
def test_student_create_get_delete(client, admin_headers, temp_student):
    got = client.get(f"/api/students/{temp_student['student_id']}", headers=admin_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Smoke Student"
    assert got.json()["registration_no"].startswith("REG-")


def test_student_search_case_insensitive_partial(client, admin_headers, temp_student):
    resp = client.get("/api/students", headers=admin_headers, params={"search": "smoke stud"})
    assert resp.status_code == 200
    assert any(s["student_id"] == temp_student["student_id"] for s in resp.json())


# --------------------------------------------------------------------- fees
def test_fee_voucher_generate_pay_and_status(client, admin_headers, temp_student):
    sid = temp_student["student_id"]
    gen = client.post(
        "/api/fee-vouchers/generate", headers=admin_headers,
        json={"student_id": sid, "year": 2026, "month": 1, "total_amount": 1000},
    )
    assert gen.status_code == 200, gen.text
    voucher = gen.json()
    assert voucher["status"] == "Unpaid"

    pay = client.post(
        f"/api/fee-vouchers/{voucher['voucher_id']}/pay", headers=admin_headers, json={"amount": 400},
    )
    assert pay.status_code == 200
    assert pay.json()["status"] == "Partial"

    overpay = client.post(
        f"/api/fee-vouchers/{voucher['voucher_id']}/pay", headers=admin_headers, json={"amount": 99999},
    )
    assert overpay.status_code == 400  # cannot exceed remaining balance


def test_voucher_pdf_streams(client, admin_headers, temp_student):
    sid = temp_student["student_id"]
    gen = client.post(
        "/api/fee-vouchers/generate", headers=admin_headers,
        json={"student_id": sid, "year": 2026, "month": 2, "total_amount": 1000},
    )
    voucher_id = gen.json()["voucher_id"]
    pdf = client.get(f"/api/fee-vouchers/{voucher_id}/pdf", headers=admin_headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"


# --------------------------------------------------------------- attendance
def test_attendance_mark_and_absent_today(client, admin_headers, temp_student):
    sid = temp_student["student_id"]
    today = date.today().isoformat()
    mark = client.post(
        "/api/attendance/mark", headers=admin_headers,
        json={"class_name": TEST_CLASS, "attendance_date": today,
              "entries": [{"student_id": sid, "status": "Absent"}]},
    )
    assert mark.status_code == 200
    absent = client.get("/api/attendance/absent-today", headers=admin_headers, params={"class_name": TEST_CLASS})
    assert absent.status_code == 200
    assert any(r["student_id"] == sid for r in absent.json())


# ------------------------------------------------------------------- reports
def test_pending_fee_report(client, admin_headers):
    resp = client.get("/api/fee-reports/pending", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# --------------------------------------------------------------- permissions

def test_accountant_cannot_delete_student(client, accountant_headers, temp_student):
    resp = client.delete(f"/api/students/{temp_student['student_id']}", headers=accountant_headers)
    assert resp.status_code == 403


def test_teacher_students_default_to_own_class(client, teacher_headers, temp_student):
    # With no class_filter, a Teacher's list defaults to their assigned class.
    own = client.get("/api/students", headers=teacher_headers)
    assert own.status_code == 200
    assert all(s["class_name"] == TEST_CLASS for s in own.json())
    # Teachers may request any other class (needed to cover its attendance).
    other = client.get("/api/students", headers=teacher_headers, params={"class_filter": "Grade 1"})
    assert other.status_code == 200


def test_teacher_can_query_any_class_attendance(client, teacher_headers):
    # Teachers may query attendance for any class, not just their own.
    resp = client.get("/api/attendance/absent-today", headers=teacher_headers, params={"class_name": "Grade 1"})
    assert resp.status_code == 200


def test_accountant_can_mark_attendance(client, accountant_headers, temp_student):
    sid = temp_student["student_id"]
    today = date.today().isoformat()
    resp = client.post(
        "/api/attendance/mark", headers=accountant_headers,
        json={"class_name": TEST_CLASS, "attendance_date": today,
              "entries": [{"student_id": sid, "status": "Present"}]},
    )
    assert resp.status_code == 200


def test_backup_requires_admin(client, accountant_headers):
    assert client.get("/api/backup/database", headers=accountant_headers).status_code == 403


# ------------------------------------------------------------- fee audit log
def test_fee_audit_records_payment_and_discount(client, admin_headers, temp_student):
    sid = temp_student["student_id"]
    gen = client.post(
        "/api/fee-vouchers/generate", headers=admin_headers,
        json={"student_id": sid, "year": 2026, "month": 3, "total_amount": 1000},
    )
    vid = gen.json()["voucher_id"]
    assert client.post(f"/api/fee-vouchers/{vid}/pay", headers=admin_headers, json={"amount": 300}).status_code == 200
    assert client.post(
        f"/api/fee-vouchers/{vid}/discount", headers=admin_headers,
        json={"amount": 100, "reason": "Sibling concession"},
    ).status_code == 200

    log = client.get("/api/fee-audit", headers=admin_headers)
    assert log.status_code == 200
    entries = log.json()
    assert any(e["action"] == "payment" and e["student_id"] == sid for e in entries)
    disc = [e for e in entries if e["action"] == "discount" and e["student_id"] == sid]
    assert disc and disc[0]["reason"] == "Sibling concession" and disc[0]["actor_username"]


def test_fee_audit_is_admin_only(client, accountant_headers):
    assert client.get("/api/fee-audit", headers=accountant_headers).status_code == 403
