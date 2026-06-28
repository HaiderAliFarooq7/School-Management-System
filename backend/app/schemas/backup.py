from pydantic import BaseModel


class ResetRequest(BaseModel):
    confirm: bool = False
