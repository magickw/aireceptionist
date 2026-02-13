from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class CallSessionBase(BaseModel):
    customer_phone: Optional[str] = None
    status: Optional[str] = "active"
    duration_seconds: Optional[int] = None
    ai_confidence: Optional[Decimal] = None
    summary: Optional[str] = None

class CallSessionCreate(CallSessionBase):
    business_id: int
    id: str # Call ID is usually a UUID string from Twilio

class CallSessionUpdate(CallSessionBase):
    ended_at: Optional[datetime] = None

class CallSessionInDBBase(CallSessionBase):
    id: str
    business_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CallSession(CallSessionInDBBase):
    pass
