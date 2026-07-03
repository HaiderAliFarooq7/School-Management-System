"""Live multi-tenant integration tests.

Runs against a RUNNING deployment (sandbox or production) over HTTP:

    SMS_BASE_URL=http://localhost:8001 SMS_SUPER_PASSWORD=Admin@123 \
        python -m pytest tests/test_multitenant_live.py -q

Covers: super admin login, school provisioning, per-school admin/teacher/
accountant logins, JWT tenant pinning, database isolation, permissions,
school switching, disable/archive, username collisions, and end-to-end
CRUD (students, fees, attendance) inside a freshly provisioned tenant.

Self-cleaning where possible: schools created here are archived at the end
(physical databases are retained by design). Skipped entirely unless
SMS_BASE_URL is set, so the regular smoke suite is unaffected.
"""
import os
import uuid

import httpx
import pytest

BASE = os.environ.get("SMS_BASE_URL")
SUPER_PASSWORD = os.environ.get("SMS_SUPER_PASSWORD", "Admin@123")

pytestmark = pytest.mark.skipif(not BASE, reason="SMS_BASE_URL not set (live integration test)")

# Unique suffix so repeated runs never collide on usernames/db names.
RUN = uuid.uuid4().hex[:6]
SCHOOL2 = {
    "school_name": "Bright Future High School",
    "campus_name": "Raabia Campus",
    "database_name": f"test_raabia_{RUN}",
    "admin_username": f"raabiaadmin_{RUN}",
    "admin_password": "Admin@123x",
}
SCHOOL3 = {
    "school_name": "The Smart School",
    "campus_name": "Main Campus",
    "database_name": f"test_smart_{RUN}",
    "admin_username": f"smartadmin_{RUN}",
    "admin_password": "Admin@123x",
}

_state: dict = {}


def client() -> httpx.Client:
    return httpx.Client(base_url=f"{BASE}/api", timeout=120)


def login(username: str, password: str) -> dict:
    with client() as c:
        r = c.post("/auth/login", json={"username": username, "password": password})
    return {"status": r.status_code, **(r.json() if r.status_code < 500 else {})}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_01_super_admin_login():
    res = login("superadmin", SUPER_PASSWORD)
    assert res["status"] == 200, res
    assert res["is_super"] is True
    assert res["role"] == "Admin"
    assert res["school_id"] is not None
    _state["super"] = res


def test_02_super_admin_can_list_schools():
    with client() as c:
        r = c.get("/master/schools", headers=auth(_state["super"]["access_token"]))
    assert r.status_code == 200
    assert len(r.json()) >= 1
    _state["initial_schools"] = r.json()


def test_03_create_school_2_and_3():
    with client() as c:
        for spec, key in ((SCHOOL2, "school2"), (SCHOOL3, "school3")):
            r = c.post("/master/schools", json=spec, headers=auth(_state["super"]["access_token"]))
            assert r.status_code == 201, r.text
            body = r.json()
            assert body["database_status"] == "active"
            assert body["database_name"] == spec["database_name"]
            _state[key] = body


def test_04_school_admin_logins_route_to_their_school():
    r2 = login(SCHOOL2["admin_username"], SCHOOL2["admin_password"])
    r3 = login(SCHOOL3["admin_username"], SCHOOL3["admin_password"])
    assert r2["status"] == 200 and r3["status"] == 200
    assert r2["school_id"] == _state["school2"]["school_id"]
    assert r3["school_id"] == _state["school3"]["school_id"]
    assert r2["is_super"] is False
    assert r2["campus_name"] == "Raabia Campus"
    _state["admin2"], _state["admin3"] = r2, r3


def test_05_fresh_tenants_start_empty():
    for key in ("admin2", "admin3"):
        with client() as c:
            r = c.get("/students", headers=auth(_state[key]["access_token"]))
        assert r.status_code == 200
        assert r.json() == [], f"{key} should see an empty school"


def test_06_seed_staff_and_students_per_school():
    """Creates teacher/accountant + 10 students in each new school via the
    normal APIs — proving full CRUD works inside freshly provisioned DBs."""
    for key, n, spec in (("admin2", 2, SCHOOL2), ("admin3", 3, SCHOOL3)):
        token = _state[key]["access_token"]
        with client() as c:
            r = c.post("/grades", json={"class_name": "Grade 1", "fee_amount": 1500}, headers=auth(token))
            assert r.status_code == 200, r.text
            for role, username, pw in (
                ("Teacher", f"teacher{n}_{RUN}", "Teacher@123"),
                ("Accountant", f"account{n}_{RUN}", "Account@123"),
            ):
                r = c.post("/users", json={
                    "username": username, "full_name": f"{role} {n}", "password": pw,
                    "role_name": role, "assigned_class_name": "Grade 1" if role == "Teacher" else None,
                }, headers=auth(token))
                assert r.status_code == 200, r.text
            for i in range(1, 11):
                r = c.post("/students", json={
                    "name": f"Student {n}-{i}", "father_name": f"Father {n}-{i}",
                    "class_name": "Grade 1", "status": "Active",
                }, headers=auth(token))
                assert r.status_code == 200, r.text
            r = c.get("/students", headers=auth(token))
            assert len(r.json()) == 10


def test_07_database_isolation_between_schools():
    with client() as c:
        s2 = c.get("/students", headers=auth(_state["admin2"]["access_token"])).json()
        s3 = c.get("/students", headers=auth(_state["admin3"]["access_token"])).json()
    names2 = {s["name"] for s in s2}
    names3 = {s["name"] for s in s3}
    assert names2 and names3
    assert names2.isdisjoint(names3), "cross-school student leakage!"
    # Registration numbers restart per school — same numbers, different DBs.
    assert {s["registration_no"] for s in s2} == {s["registration_no"] for s in s3}


def test_08_teacher_and_accountant_logins_and_permissions():
    t = login(f"teacher2_{RUN}", "Teacher@123")
    a = login(f"account2_{RUN}", "Account@123")
    assert t["status"] == 200 and a["status"] == 200
    assert t["school_id"] == _state["school2"]["school_id"]
    assert t["role"] == "Teacher" and a["role"] == "Accountant"
    with client() as c:
        # Teacher may read their class roster but never create students.
        r = c.get("/students", headers=auth(t["access_token"]))
        assert r.status_code == 200
        r = c.post("/students", json={"name": "X", "father_name": "Y", "class_name": "Grade 1"},
                   headers=auth(t["access_token"]))
        assert r.status_code == 403
        # Accountant cannot manage users.
        r = c.get("/users", headers=auth(a["access_token"]))
        assert r.status_code == 403
        # Neither can touch the master API.
        for tok in (t["access_token"], a["access_token"], _state["admin2"]["access_token"]):
            r = c.get("/master/schools", headers=auth(tok))
            assert r.status_code == 403, "non-super user reached the master API!"


def test_09_tampered_token_is_rejected():
    """Re-signing the JWT with a different key must yield 401 — the school_id
    claim cannot be forged without the server's secret."""
    from jose import jwt as jose_jwt
    token = _state["admin2"]["access_token"]
    payload = jose_jwt.get_unverified_claims(token)
    payload["school_id"] = _state["initial_schools"][0]["school_id"]  # try to hop tenants
    forged = jose_jwt.encode(payload, "wrong-secret", algorithm="HS256")
    with client() as c:
        r = c.get("/students", headers=auth(forged))
    assert r.status_code == 401


def test_10_super_admin_school_switching():
    token = _state["super"]["access_token"]
    with client() as c:
        r = c.post(f"/master/switch/{_state['school2']['school_id']}", headers=auth(token))
        assert r.status_code == 200
        switched = r.json()
        assert switched["school_id"] == _state["school2"]["school_id"]
        # The switched token sees school 2's data...
        students = c.get("/students", headers=auth(switched["access_token"])).json()
        assert {s["name"] for s in students} == {f"Student 2-{i}" for i in range(1, 11)}
        # ...and school 2's own profile/settings.
        profile = c.get("/school", headers=auth(switched["access_token"])).json()
        assert "Raabia" in (profile["name"] or "")


def test_11_fees_and_attendance_inside_new_tenant():
    token = _state["admin2"]["access_token"]
    with client() as c:
        students = c.get("/students", headers=auth(token)).json()
        sid = students[0]["student_id"]
        r = c.post("/fee-vouchers/generate",
                   json={"student_id": sid, "year": 2026, "month": 7, "total_amount": 1500},
                   headers=auth(token))
        assert r.status_code == 200, r.text
        voucher = r.json()
        r = c.post(f"/fee-vouchers/{voucher['voucher_id']}/pay", json={"amount": 500}, headers=auth(token))
        assert r.status_code == 200 and r.json()["status"] == "Partial"
        # Attendance (teacher marks their class)
        t = login(f"teacher2_{RUN}", "Teacher@123")
        r = c.post("/attendance/mark", json={
            "class_name": "Grade 1", "attendance_date": "2026-07-03", "period_name": "Full Day",
            "entries": [{"student_id": sid, "status": "Present"}],
        }, headers=auth(t["access_token"]))
        assert r.status_code == 200, r.text
        # None of this leaked into school 3.
        r = c.get("/fee-vouchers", params={"class_name": "Grade 1"}, headers=auth(_state["admin3"]["access_token"]))
        assert r.status_code == 200 and r.json() == []


def test_12_username_collision_across_schools_rejected():
    with client() as c:
        r = c.post("/users", json={
            "username": SCHOOL3["admin_username"],  # already routed to school 3
            "full_name": "Impostor", "password": "Whatever@123", "role_name": "Teacher",
        }, headers=auth(_state["admin2"]["access_token"]))
    assert r.status_code == 409


def test_13_disable_blocks_login_and_requests():
    sup = _state["super"]["access_token"]
    sid3 = _state["school3"]["school_id"]
    with client() as c:
        r = c.patch(f"/master/schools/{sid3}/status", json={"database_status": "disabled"}, headers=auth(sup))
        assert r.status_code == 200
        # login blocked
        res = login(SCHOOL3["admin_username"], SCHOOL3["admin_password"])
        assert res["status"] == 403
        # existing token blocked too
        r = c.get("/students", headers=auth(_state["admin3"]["access_token"]))
        assert r.status_code == 403
        # re-activate
        r = c.patch(f"/master/schools/{sid3}/status", json={"database_status": "active"}, headers=auth(sup))
        assert r.status_code == 200
        assert login(SCHOOL3["admin_username"], SCHOOL3["admin_password"])["status"] == 200


def test_14_stats_endpoints():
    sup = _state["super"]["access_token"]
    with client() as c:
        r = c.get(f"/master/schools/{_state['school2']['school_id']}/stats", headers=auth(sup))
        assert r.status_code == 200
        body = r.json()
        assert body["total_students"] == 10 and body["users"] >= 3 and body["reachable"] is True
        r = c.get("/master/stats", headers=auth(sup))
        assert r.status_code == 200 and r.json()["total_schools"] >= 3


def test_15_archive_school_keeps_database():
    """'Delete' archives the school: hidden + logins blocked, DB retained."""
    sup = _state["super"]["access_token"]
    with client() as c:
        for key in ("school2", "school3"):
            r = c.delete(f"/master/schools/{_state[key]['school_id']}", headers=auth(sup))
            assert r.status_code == 200 and r.json()["database_status"] == "archived"
        res = login(SCHOOL2["admin_username"], SCHOOL2["admin_password"])
        assert res["status"] == 403
        # Master still lists them (archived), proving nothing was dropped.
        rows = c.get("/master/schools", headers=auth(sup)).json()
        by_id = {s["school_id"]: s for s in rows}
        assert by_id[_state["school2"]["school_id"]]["database_status"] == "archived"
