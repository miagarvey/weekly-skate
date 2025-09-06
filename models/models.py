from pydantic import BaseModel, field_validator

def is_e164(phone: str) -> bool:
    """Check if phone number is in E.164 format"""
    phone = phone.strip()
    return phone.startswith("+") and phone[1:].isdigit() and 8 <= len(phone) <= 16

class Signup(BaseModel):
    name: str
    phone: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name required")
        return v

    @field_validator("phone")
    @classmethod
    def phone_e164_or_blank(cls, v):
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if is_e164(v):
            return v
        raise ValueError("Phone must be +E.164 like +15551234567 or leave blank")
