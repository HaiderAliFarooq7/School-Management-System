from pydantic import BaseModel, ConfigDict, Field


class VoucherOut(BaseModel):
    voucher_id: int
    student_id: int
    fee_month: str
    fee_month_sort: str
    total_amount: float
    paid_amount: float
    discount_amount: float
    discount_reason: str | None = None
    remaining: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class VoucherWithStudentOut(VoucherOut):
    student_name: str
    registration_no: str


class GenerateVoucherRequest(BaseModel):
    student_id: int
    year: int
    month: int = Field(ge=1, le=12)
    total_amount: float = Field(ge=0)


class BulkGenerateRequest(BaseModel):
    class_names: list[str]
    year: int
    month: int = Field(ge=1, le=12)


class PayVoucherRequest(BaseModel):
    amount: float = Field(gt=0)


class BulkPayRequest(BaseModel):
    class_name: str
    year: int
    month: int = Field(ge=1, le=12)
    amount_per_student: float = Field(gt=0)


class DiscountRequest(BaseModel):
    amount: float = Field(gt=0)
    reason: str = ""


class VoucherEditRequest(BaseModel):
    """Admin-only direct edit — can override a voucher's figures even after
    payments/discounts have been recorded against it."""
    total_amount: float = Field(ge=0)
    paid_amount: float = Field(ge=0)
    discount_amount: float = Field(default=0, ge=0)
    discount_reason: str | None = None


class SelectedVouchersPdfRequest(BaseModel):
    voucher_ids: list[int]
    mode: str = "4up"  # "4up" | "individual"


class VoucherSearchResult(BaseModel):
    voucher_id: int
    student_id: int
    registration_no: str
    name: str
    class_name: str
    phone: str | None
    cnic: str | None
    fee_month: str
    total_amount: float
    paid_amount: float
    discount_amount: float
    status: str
    other_pending: float


class VoucherFilterRow(VoucherWithStudentOut):
    is_overdue: bool
    charges_pending: float


class BulkDeleteVouchersRequest(BaseModel):
    voucher_ids: list[int]


class BulkDeleteResult(BaseModel):
    deleted: int
    skipped: list[dict]
