from pydantic import BaseModel, ConfigDict


class GradeCreate(BaseModel):
    class_name: str
    fee_amount: float = 0


class GradeUpdate(BaseModel):
    class_name: str
    fee_amount: float


class GradeOut(BaseModel):
    grade_id: int
    class_name: str
    fee_amount: float
    student_count: int = 0

    model_config = ConfigDict(from_attributes=True)
