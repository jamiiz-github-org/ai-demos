from pydantic import BaseModel, EmailStr, Field


class LeadRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    business: str | None = None
    pain_point: str | None = None
    hours_saved: str | None = None   # "5-10 hours/week", etc.
    assistant: str | None = None
    session_id: str | None = None


class LeadResponse(BaseModel):
    id: int
    message: str = "Thanks! We'll be in touch shortly."
