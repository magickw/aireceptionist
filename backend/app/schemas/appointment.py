from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AppointmentBase(BaseModel):
    customer_name: str
    customer_phone: str
    appointment_time: datetime
    service_type: Optional[str] = None
    status: Optional[str] = "scheduled"
    source: Optional[str] = "internal"

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
