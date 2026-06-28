from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChargeOut(BaseModel):
    charge_id: int
    student_id: int
    description: str
    amount: float
    paid_amount: float
    remaining_amount: float
    discount_amount: float
    discount_reason: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChargeCreate(BaseModel):
    student_id: int
    description: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)


class PayChargeRequest(BaseModel):
    amount: float = Field(gt=0)


class DiscountChargeRequest(BaseModel):
    amount: float = Field(gt=0)
    reason: str = ""


class BulkChargeRequest(BaseModel):
    class_names: list[str]
    description: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)


class BulkDeleteChargesRequest(BaseModel):
    charge_ids: list[int]


class ChargeEditRequest(BaseModel):
    """Admin-only direct edit — can override a charge's figures even after
    payments/discounts have been recorded against it."""
    description: str = Field(min_length=1, max_length=255)
    amount: float = Field(ge=0)
    paid_amount: float = Field(ge=0)
    discount_amount: float = Field(default=0, ge=0)
    discount_reason: str | None = None


class BulkDeleteChargesResult(BaseModel):
    deleted: int
    skipped: list[dict]
