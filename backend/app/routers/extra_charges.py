from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models.extra_charge import ExtraCharge
from app.models.payment_history import PaymentHistory
from app.models.student import Student
from app.services import audit_service
from app.schemas.extra_charge import (
    BulkChargeRequest,
    BulkDeleteChargesRequest,
    BulkDeleteChargesResult,
    ChargeCreate,
    ChargeEditRequest,
    ChargeOut,
    DiscountChargeRequest,
    PayChargeRequest,
)

router = APIRouter(
    prefix="/api/extra-charges",
    tags=["extra_charges"],
    dependencies=[Depends(require_role("Admin", "Accountant"))],
)
require_admin = Depends(require_role("Admin"))


@router.post("", response_model=ChargeOut)
def add_charge(payload: ChargeCreate, db: Session = Depends(get_db)):
    if payload.amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Charge amount must be greater than zero.")
    charge = ExtraCharge(
        student_id=payload.student_id,
        description=payload.description,
        amount=payload.amount,
        paid_amount=0,
        remaining_amount=payload.amount,
        status="Open",
    )
    db.add(charge)
    db.commit()
    return charge


@router.post("/bulk", response_model=list[ChargeOut])
def bulk_add_charge(payload: BulkChargeRequest, db: Session = Depends(get_db)):
    """Add the same charge (description + amount) to every active student
    in the selected classes — one charge per student, in a single request."""
    if payload.amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Charge amount must be greater than zero.")
    students = db.execute(
        select(Student).where(Student.class_name.in_(payload.class_names), Student.status == "Active")
    ).scalars().all()
    charges = [
        ExtraCharge(
            student_id=s.student_id,
            description=payload.description,
            amount=payload.amount,
            paid_amount=0,
            remaining_amount=payload.amount,
            status="Open",
        )
        for s in students
    ]
    db.add_all(charges)
    db.commit()
    return charges


@router.post("/{charge_id}/pay", response_model=ChargeOut)
def pay_charge(
    charge_id: int, payload: PayChargeRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if payload.amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment amount must be greater than zero.")
    # Row lock — same concurrent-payment guard as pay_voucher.
    charge = db.execute(
        select(ExtraCharge).where(ExtraCharge.charge_id == charge_id).with_for_update()
    ).scalar_one_or_none()
    if charge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charge not found")
    if payload.amount > float(charge.remaining_amount) + 1e-6:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Payment exceeds remaining balance of {float(charge.remaining_amount):.2f}.",
        )
    new_paid = float(charge.paid_amount) + payload.amount
    new_remaining = round(float(charge.amount) - new_paid, 2)
    charge.paid_amount = new_paid
    charge.remaining_amount = max(new_remaining, 0)
    charge.status = "Paid" if new_remaining <= 0 else "Open"
    db.add(PaymentHistory(target_type="extra_charge", target_id=charge_id, amount=payload.amount, paid_at=datetime.now()))
    audit_service.record(
        db, current_user, action="payment", target_type="extra_charge", target_id=charge_id,
        student=db.get(Student, charge.student_id), label=charge.description, amount=payload.amount,
    )
    db.commit()
    return charge


@router.post("/{charge_id}/discount", response_model=ChargeOut, dependencies=[require_admin])
def apply_discount(
    charge_id: int, payload: DiscountChargeRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if payload.amount < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Discount amount cannot be negative.")
    charge = db.get(ExtraCharge, charge_id)
    if charge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charge not found")
    max_discount = float(charge.amount) - float(charge.paid_amount)
    if payload.amount > max_discount + 1e-6:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Discount cannot exceed the unpaid balance of {max_discount:.2f}.",
        )
    charge.discount_amount = payload.amount
    charge.discount_reason = payload.reason or None
    new_remaining = round(float(charge.amount) - float(charge.paid_amount) - payload.amount, 2)
    charge.remaining_amount = max(new_remaining, 0)
    charge.status = "Paid" if new_remaining <= 0 else "Open"
    audit_service.record(
        db, current_user, action="discount", target_type="extra_charge", target_id=charge_id,
        student=db.get(Student, charge.student_id), label=charge.description,
        amount=payload.amount, reason=payload.reason,
    )
    db.commit()
    return charge


@router.post("/bulk-delete", response_model=BulkDeleteChargesResult, dependencies=[require_admin])
def bulk_delete_charges(
    payload: BulkDeleteChargesRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin-only: delete a hand-picked set of extra charges outright, even
    ones that already have a payment or discount recorded."""
    charges = db.execute(
        select(ExtraCharge).where(ExtraCharge.charge_id.in_(payload.charge_ids))
    ).scalars().all()
    found_ids = {c.charge_id for c in charges}
    skipped = [{"charge_id": cid, "reason": "Charge not found"} for cid in payload.charge_ids if cid not in found_ids]
    for charge in charges:
        audit_service.record(
            db, current_user, action="delete", target_type="extra_charge", target_id=charge.charge_id,
            student=db.get(Student, charge.student_id), label=charge.description,
            note=f"amount={charge.amount}, paid={charge.paid_amount}",
        )
        audit_service.void_for_target(
            db, target_type="extra_charge", target_id=charge.charge_id,
            student_id=charge.student_id, label=charge.description,
        )
        db.delete(charge)
    db.commit()
    return BulkDeleteChargesResult(deleted=len(charges), skipped=skipped)


@router.delete("/{charge_id}", dependencies=[require_admin])
def delete_charge(
    charge_id: int, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin-only: delete any charge outright, even one with payments or a
    discount already recorded — Accountants can never delete a charge."""
    charge = db.get(ExtraCharge, charge_id)
    if charge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charge not found")
    audit_service.record(
        db, current_user, action="delete", target_type="extra_charge", target_id=charge_id,
        student=db.get(Student, charge.student_id), label=charge.description,
        note=f"amount={charge.amount}, paid={charge.paid_amount}",
    )
    # Void this charge's payments so they leave the collections totals.
    audit_service.void_for_target(
        db, target_type="extra_charge", target_id=charge_id,
        student_id=charge.student_id, label=charge.description,
    )
    db.delete(charge)
    db.commit()
    return {"detail": "Deleted"}


@router.put("/{charge_id}", response_model=ChargeOut, dependencies=[require_admin])
def edit_charge(
    charge_id: int, payload: ChargeEditRequest, db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Admin-only: directly overwrite a charge's figures, including ones that
    are already fully paid."""
    charge = db.get(ExtraCharge, charge_id)
    if charge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charge not found")
    charge.description = payload.description
    charge.amount = payload.amount
    charge.paid_amount = payload.paid_amount
    charge.discount_amount = payload.discount_amount
    charge.discount_reason = payload.discount_reason
    remaining = round(payload.amount - payload.paid_amount - payload.discount_amount, 2)
    charge.remaining_amount = max(remaining, 0)
    charge.status = "Paid" if remaining <= 0 else "Open"
    audit_service.record(
        db, current_user, action="edit", target_type="extra_charge", target_id=charge_id,
        student=db.get(Student, charge.student_id), label=payload.description,
        amount=payload.amount, reason=payload.discount_reason,
        note=f"amount={payload.amount}, paid={payload.paid_amount}, discount={payload.discount_amount}",
    )
    db.commit()
    return charge
