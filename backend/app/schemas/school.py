from pydantic import BaseModel, ConfigDict


class SchoolUpdate(BaseModel):
    name: str
    address: str
    phone: str
    logo_path: str | None = None
    bank_name: str
    account_title: str
    account_number: str
    iban: str
    fee_due_day: int = 10
    challan_note: str | None = None


class SchoolOut(SchoolUpdate):
    school_id: int

    model_config = ConfigDict(from_attributes=True)
