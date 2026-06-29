from pydantic import BaseModel, ConfigDict


class SchoolUpdate(BaseModel):
    """Fields editable via PUT /school. logo_path is deliberately excluded —
    it's server-managed exclusively by POST /school/logo, so a settings save
    can never accidentally clobber it (see router for why this matters)."""
    name: str
    address: str
    phone: str
    bank_name: str
    account_title: str
    account_number: str
    iban: str
    fee_due_day: int = 10
    challan_note: str | None = None


class SchoolOut(SchoolUpdate):
    school_id: int
    logo_path: str | None = None

    model_config = ConfigDict(from_attributes=True)
