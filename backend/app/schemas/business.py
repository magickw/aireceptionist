from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

VALID_BUSINESS_TYPES = [
    "general",
    "restaurant",
    "healthcare",
    "legal",
    "real_estate",
    "automotive",
    "salon",
    "dental",
    "veterinary",
    "fitness",
    "hotel",
    "insurance",
    "financial",
    "education",
    "construction",
    "plumbing",
    "electrical",
    "hvac",
    "cleaning",
    "landscaping",
    "pest_control",
    "roofing",
    "painting",
    "moving",
    "storage",
    "pet_care",
    "photography",
    "event_planning",
    "travel",
    "retail",
    "pharmacy",
    "optometry",
    "chiropractic",
    "physical_therapy",
    "mental_health",
    "accounting",
    "consulting",
    "marketing",
    "it_services",
    "staffing",
]

class BusinessBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: Optional[str] = Field("general", max_length=50)
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = "active"
    operating_hours: Optional[dict] = None
    settings: Optional[dict] = None
    business_license: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_business_type(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_BUSINESS_TYPES:
            raise ValueError(f"Invalid business type. Must be one of: {', '.join(VALID_BUSINESS_TYPES)}")
        return v

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    pass

class BusinessInDBBase(BusinessBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Business(BusinessInDBBase):
    pass
