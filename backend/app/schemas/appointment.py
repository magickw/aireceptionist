import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class AppointmentBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: str = Field(..., min_length=7, max_length=20)
    appointment_time: datetime
    service_type: Optional[str] = None
    status: Optional[str] = Field("scheduled", pattern=r"^(scheduled|completed|cancelled|no_show)$")
    source: Optional[str] = "internal"

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^\+?\d{7,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return v

class AppointmentCreate(AppointmentBase):
    business_id: int

class AppointmentUpdate(AppointmentBase):
    pass

class AppointmentInDBBase(AppointmentBase):
    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Appointment(AppointmentInDBBase):
    pass
