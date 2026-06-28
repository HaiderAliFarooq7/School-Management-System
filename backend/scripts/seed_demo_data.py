"""
Seed comprehensive demo data: students across grades, attendance, varied fee states.
Safe to run multiple times — skips existing students by registration number.
"""
from datetime import date, timedelta
from app.db.session import SessionLocal
from app.models.student import Student
from app.models.attendance import AttendanceRecord
from app.models.fee_voucher import FeeVoucher
from app.models.grade import Grade

db = SessionLocal()

# Student data: name, father_name, class_name, phone, status
STUDENT_DATA = [
    ("Ali Khan", "Ahmad Khan", "Prep", "0300-1234567", "Active"),
    ("Sara Ahmed", "Mohammed Ahmed", "Grade 1", "0301-2345678", "Active"),
    ("Haider Ali", "Hassan Ali", "Grade 2", "0302-3456789", "Active"),
    ("Ahmed Raza", "Raza Ali", "Grade 2", "0303-4567890", "Active"),
    ("Fatima Noor", "Noor Hassan", "Grade 1", "0304-5678901", "Active"),
    ("Bilal Hussain", "Hussain Khan", "Prep", "0305-6789012", "Active"),
    ("Aisha Khan", "Ali Khan", "Grade 3", "0306-7890123", "Active"),
    ("Zainab Ahmed", "Ahmed Malik", "Grade 3", "0307-8901234", "Active"),
    ("Hassan Raza", "Raza Khan", "Grade 1", "0308-9012345", "Active"),
    ("Maryam Noor", "Noor Ali", "Grade 2", "0309-0123456", "Active"),
    ("Tariq Hassan", "Hassan Khan", "Prep", "0310-1234567", "Active"),
    ("Laila Ahmed", "Ahmed Khan", "Grade 3", "0311-2345678", "Active"),
    ("Karim Ali", "Ali Hassan", "Grade 1", "0312-3456789", "Active"),
    ("Noor Khan", "Khan Malik", "Grade 2", "0313-4567890", "Active"),
    ("Amina Malik", "Malik Hassan", "Prep", "0314-5678901", "Active"),
]

existing_count = db.query(Student).count()
print(f"Existing students: {existing_count}")

for i, (name, father_name, class_name, phone, status) in enumerate(STUDENT_DATA, start=existing_count + 1):
    reg_num = f"REG-{i:04d}"
    # Check if already exists
    if db.query(Student).filter_by(registration_no=reg_num).first():
        print(f"  Skipped {reg_num} (already exists)")
        continue

    grade = db.query(Grade).filter_by(class_name=class_name).first()
    if not grade:
        print(f"  Skipped {reg_num} (grade '{class_name}' not found)")
        continue

    student = Student(
        registration_no=reg_num,
        name=name,
        father_name=father_name,
        dob=date.today().replace(year=date.today().year - 8),
        address=f"{class_name}, School",
        class_name=class_name,
        phone=phone,
        status=status,
    )
    db.add(student)
    db.flush()
    print(f"  Added {reg_num}: {name} ({class_name})")

    # Create vouchers for this student (Jan, Apr, Jul, Oct)
    import random
    months_data = [
        (1, "January", "2026-01"),
        (4, "April", "2026-04"),
        (7, "July", "2026-07"),
        (10, "October", "2026-10"),
    ]
    for month_num, month_name, month_sort in months_data:
        # Mix of Unpaid, Partial, and Paid
        status_choice = random.choice(["Unpaid", "Unpaid", "Partial", "Paid"])
        paid = 0
        if status_choice == "Partial":
            paid = float(grade.fee_amount) * random.uniform(0.3, 0.7)
        elif status_choice == "Paid":
            paid = float(grade.fee_amount)

        voucher = FeeVoucher(
            student_id=student.student_id,
            fee_month=f"{month_name} 2026",
            fee_month_sort=month_sort,
            total_amount=float(grade.fee_amount),
            paid_amount=paid,
            discount_amount=0,
            status=status_choice,
        )
        db.add(voucher)

    # Add a few random attendance records for this student (last 7 days, mix of present/absent)
    for days_ago in range(1, 8):
        record_date = date.today() - timedelta(days=days_ago)
        is_present = random.choice([True, True, True, False])  # 75% present
        attendance = AttendanceRecord(
            student_id=student.student_id,
            class_name=class_name,
            attendance_date=record_date,
            period_name="Full Day",
            status="Present" if is_present else "Absent",
            remarks="",
        )
        db.add(attendance)

db.commit()
print("\nDemo data seeded successfully!")
print(f"Total students now: {db.query(Student).count()}")
print(f"Total vouchers now: {db.query(FeeVoucher).count()}")
print(f"Total attendance records now: {db.query(AttendanceRecord).count()}")
db.close()
