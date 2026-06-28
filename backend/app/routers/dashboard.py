from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.extra_charge import ExtraCharge
from app.models.fee_voucher import FeeVoucher
from app.models.grade import Grade
from app.models.student import Student

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_role("Admin", "Accountant"))],
)


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    total_students = db.execute(
        select(func.count()).select_from(Student).where(Student.status == "Active")
    ).scalar_one()
    total_classes = db.execute(select(func.count()).select_from(Grade)).scalar_one()
    by_class = db.execute(
        select(Student.class_name, func.count())
        .where(Student.status == "Active")
        .group_by(Student.class_name)
        .order_by(Student.class_name)
    ).all()

    if current_user.role_name != "Admin":
        # Accountant gets headcounts only — no combined fee figures of any kind.
        return {
            "total_students": total_students,
            "total_classes": total_classes,
            "total_collected": None,
            "total_discounted": None,
            "total_outstanding": None,
            "outstanding_charges": None,
            "by_class": [{"class_name": c, "count": n} for c, n in by_class],
        }

    total_collected = db.execute(select(func.coalesce(func.sum(FeeVoucher.paid_amount), 0))).scalar_one()
    total_discounted = db.execute(select(func.coalesce(func.sum(FeeVoucher.discount_amount), 0))).scalar_one()
    total_outstanding = db.execute(
        select(func.coalesce(func.sum(FeeVoucher.total_amount - FeeVoucher.paid_amount - FeeVoucher.discount_amount), 0))
    ).scalar_one()
    outstanding_charges = db.execute(
        select(func.coalesce(func.sum(ExtraCharge.remaining_amount), 0)).where(ExtraCharge.status != "Paid")
    ).scalar_one()

    return {
        "total_students": total_students,
        "total_classes": total_classes,
        "total_collected": float(total_collected),
        "total_discounted": float(total_discounted),
        "total_outstanding": float(total_outstanding),
        "outstanding_charges": float(outstanding_charges),
        "by_class": [{"class_name": c, "count": n} for c, n in by_class],
    }


@router.get("/class-collection-progress", dependencies=[Depends(require_role("Admin"))])
def get_class_collection_progress(db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            Grade.class_name,
            func.coalesce(func.sum(FeeVoucher.total_amount), 0),
            func.coalesce(func.sum(FeeVoucher.paid_amount), 0),
        )
        .outerjoin(Student, (Student.class_name == Grade.class_name) & (Student.status == "Active"))
        .outerjoin(FeeVoucher, FeeVoucher.student_id == Student.student_id)
        .group_by(Grade.class_name)
        .order_by(Grade.class_name)
    ).all()
    result = []
    for class_name, total, collected in rows:
        total = float(total)
        collected = float(collected)
        pct = (collected / total * 100) if total > 0 else 0
        result.append({"class_name": class_name, "total": total, "collected": collected, "pct": pct})
    return result
