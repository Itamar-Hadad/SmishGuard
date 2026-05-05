from pydantic import BaseModel, field_validator


class SMSRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v.strip()


class SMSResponse(BaseModel):
    is_smishing: bool
    confidence: float
    label: str
    reason: str
