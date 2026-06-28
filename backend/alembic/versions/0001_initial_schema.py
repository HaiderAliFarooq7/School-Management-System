"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-24

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role",
        sa.Column("role_id", sa.Integer, primary_key=True),
        sa.Column("role_name", sa.String(30), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
    )

    op.create_table(
        "school",
        sa.Column("school_id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("address", sa.Text, nullable=False, server_default=""),
        sa.Column("phone", sa.String(50), nullable=False, server_default=""),
        sa.Column("logo_path", sa.Text, nullable=True),
        sa.Column("bank_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("account_title", sa.String(255), nullable=False, server_default=""),
        sa.Column("account_number", sa.String(100), nullable=False, server_default=""),
        sa.Column("iban", sa.String(100), nullable=False, server_default=""),
        sa.Column("fee_due_day", sa.Integer, nullable=False, server_default="10"),
        sa.Column("sms_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("sms_gateway", sa.String(255), nullable=False, server_default=""),
        sa.Column("sms_api_key", sa.String(255), nullable=False, server_default=""),
        sa.Column("sms_api_secret", sa.String(255), nullable=False, server_default=""),
        sa.Column("sms_sender_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("smtp_server", sa.String(255), nullable=False, server_default=""),
        sa.Column("smtp_port", sa.Integer, nullable=False, server_default="587"),
        sa.Column("smtp_email", sa.String(255), nullable=False, server_default=""),
        sa.Column("smtp_password", sa.String(255), nullable=False, server_default=""),
    )

    op.create_table(
        "grade",
        sa.Column("grade_id", sa.Integer, primary_key=True),
        sa.Column("class_name", sa.String(50), nullable=False, unique=True),
        sa.Column("fee_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )

    op.create_table(
        "user_account",
        sa.Column("user_id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("role.role_id"), nullable=False),
        sa.Column(
            "assigned_class_name",
            sa.String(50),
            sa.ForeignKey("grade.class_name", onupdate="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "student",
        sa.Column("student_id", sa.Integer, primary_key=True),
        sa.Column("registration_no", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("father_name", sa.String(150), nullable=False),
        sa.Column(
            "class_name",
            sa.String(50),
            sa.ForeignKey("grade.class_name", onupdate="CASCADE"),
            nullable=False,
        ),
        sa.Column("dob", sa.Date, nullable=True),
        sa.Column("admission_date", sa.Date, nullable=True),
        sa.Column("b_form", sa.String(50), nullable=True),
        sa.Column("cnic", sa.String(50), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("photo_path", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Active"),
    )
    op.create_index("idx_student_registration_no", "student", ["registration_no"])
    op.create_index("idx_student_class_name", "student", ["class_name"])

    op.create_table(
        "fee_voucher",
        sa.Column("voucher_id", sa.Integer, primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer,
            sa.ForeignKey("student.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fee_month", sa.String(20), nullable=False),
        sa.Column("fee_month_sort", sa.String(7), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="Unpaid"),
        sa.UniqueConstraint("student_id", "fee_month"),
    )
    op.create_index("idx_fee_voucher_student_id", "fee_voucher", ["student_id"])

    op.create_table(
        "extra_charge",
        sa.Column("charge_id", sa.Integer, primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer,
            sa.ForeignKey("student.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("remaining_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="Open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_extra_charge_student_id", "extra_charge", ["student_id"])

    op.create_table(
        "payment_history",
        sa.Column("payment_id", sa.BigInteger, primary_key=True),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", sa.Integer, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "student_contact",
        sa.Column("contact_id", sa.Integer, primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer,
            sa.ForeignKey("student.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("contact_type", sa.String(20), nullable=False),
        sa.Column("contact_value", sa.String(255), nullable=False),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_student_contact_student_id", "student_contact", ["student_id"])

    op.create_table(
        "notification_log",
        sa.Column("log_id", sa.Integer, primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer,
            sa.ForeignKey("student.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(20), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_notification_log_student_id", "notification_log", ["student_id"])

    op.create_table(
        "qr_code",
        sa.Column("qr_id", sa.Integer, primary_key=True),
        sa.Column(
            "voucher_id",
            sa.Integer,
            sa.ForeignKey("fee_voucher.voucher_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("qr_code_text", sa.String(255), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_qr_code_voucher_id", "qr_code", ["voucher_id"])

    op.create_table(
        "attendance_record",
        sa.Column("attendance_id", sa.Integer, primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer,
            sa.ForeignKey("student.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "class_name",
            sa.String(50),
            sa.ForeignKey("grade.class_name", onupdate="CASCADE"),
            nullable=False,
        ),
        sa.Column("attendance_date", sa.Date, nullable=False),
        sa.Column("period_name", sa.String(50), nullable=False, server_default="Full Day"),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column(
            "marked_by_user_id", sa.Integer, sa.ForeignKey("user_account.user_id"), nullable=True
        ),
        sa.Column("marked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('Present','Absent','Late','Leave')"),
        sa.UniqueConstraint("student_id", "attendance_date", "period_name"),
    )
    op.create_index("idx_attendance_class_date", "attendance_record", ["class_name", "attendance_date"])
    op.create_index("idx_attendance_student_date", "attendance_record", ["student_id", "attendance_date"])


def downgrade() -> None:
    op.drop_table("attendance_record")
    op.drop_table("qr_code")
    op.drop_table("notification_log")
    op.drop_table("student_contact")
    op.drop_table("payment_history")
    op.drop_table("extra_charge")
    op.drop_table("fee_voucher")
    op.drop_table("student")
    op.drop_table("user_account")
    op.drop_table("grade")
    op.drop_table("school")
    op.drop_table("role")
