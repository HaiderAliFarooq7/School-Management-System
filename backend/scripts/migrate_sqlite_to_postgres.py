"""One-time cutover: copy all data from the old SMS_Python sms.db SQLite file
into the new PostgreSQL database. Run AFTER `alembic upgrade head` and AFTER
`python -m scripts.seed` (so role/school rows already exist), and BEFORE any
real web users start using the app.

Usage:
    python -m scripts.migrate_sqlite_to_postgres "C:\\Users\\OTS\\AppData\\Local\\SMS\\sms.db"
"""
import sqlite3
import sys

from sqlalchemy import text

from app.db.session import SessionLocal

# (sqlite_table, columns_in_order) -- column order must match the INSERT below
TABLES = [
    ("school", ["school_id", "name", "address", "phone", "logo_path", "bank_name",
                "account_title", "account_number", "iban", "fee_due_day",
                "sms_enabled", "sms_gateway", "sms_api_key", "sms_api_secret", "sms_sender_id",
                "email_enabled", "smtp_server", "smtp_port", "smtp_email", "smtp_password"]),
    ("grade", ["grade_id", "class_name", "fee_amount"]),
    ("student", ["student_id", "registration_no", "name", "father_name", "class_name",
                 "dob", "admission_date", "b_form", "cnic", "phone", "address",
                 "photo_path", "status"]),
    ("fee_voucher", ["voucher_id", "student_id", "fee_month", "fee_month_sort",
                     "total_amount", "paid_amount", "status"]),
    ("extra_charge", ["charge_id", "student_id", "description", "amount", "paid_amount",
                      "remaining_amount", "status", "created_at"]),
    ("payment_history", ["payment_id", "target_type", "target_id", "amount", "paid_at"]),
    ("student_contact", ["contact_id", "student_id", "contact_type", "contact_value",
                         "is_verified", "is_primary", "created_at"]),
    ("notification_log", ["log_id", "student_id", "notification_type", "message",
                          "status", "sent_at", "created_at"]),
    ("qr_code", ["qr_id", "voucher_id", "qr_code_text", "generated_at"]),
]

# (postgres_table, id_column, sequence_name)
SEQUENCES = [
    ("school", "school_id", "school_school_id_seq"),
    ("grade", "grade_id", "grade_grade_id_seq"),
    ("student", "student_id", "student_student_id_seq"),
    ("fee_voucher", "voucher_id", "fee_voucher_voucher_id_seq"),
    ("extra_charge", "charge_id", "extra_charge_charge_id_seq"),
    ("payment_history", "payment_id", "payment_history_payment_id_seq"),
    ("student_contact", "contact_id", "student_contact_contact_id_seq"),
    ("notification_log", "log_id", "notification_log_log_id_seq"),
    ("qr_code", "qr_id", "qr_code_qr_id_seq"),
]


def migrate(sqlite_path: str) -> None:
    sconn = sqlite3.connect(sqlite_path)
    sconn.row_factory = sqlite3.Row
    db = SessionLocal()

    try:
        # school row already exists from seed.py — update it instead of inserting a duplicate
        row = sconn.execute("SELECT * FROM school LIMIT 1").fetchone()
        if row is not None:
            cols = [c for c in row.keys() if c != "school_id"]
            set_clause = ", ".join(f"{c} = :{c}" for c in cols)
            params = {c: row[c] for c in cols}
            db.execute(text(f"UPDATE school SET {set_clause} WHERE school_id = 1"), params)
            db.commit()
            print("school: updated row 1")

        for table, columns in TABLES:
            if table == "school":
                continue
            rows = sconn.execute(f"SELECT * FROM {table}").fetchall()
            count = 0
            for r in rows:
                values = {c: r[c] for c in columns}
                placeholders = ", ".join(f":{c}" for c in columns)
                col_list = ", ".join(columns)
                db.execute(
                    text(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                         f"ON CONFLICT DO NOTHING"),
                    values,
                )
                count += 1
            db.commit()
            print(f"{table}: copied {count} rows")

        for table, id_col, seq_name in SEQUENCES:
            db.execute(
                text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX({id_col}) FROM {table}), 1))")
            )
        db.commit()
        print("Sequences reset to continue after migrated max IDs.")

        # Verification: row counts must match
        print("\nVerification (sqlite vs postgres row counts):")
        for table, _ in TABLES:
            s_count = sconn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            p_count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            flag = "OK" if s_count == p_count else "MISMATCH"
            print(f"  {table}: sqlite={s_count} postgres={p_count}  [{flag}]")

    finally:
        db.close()
        sconn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    migrate(sys.argv[1])
