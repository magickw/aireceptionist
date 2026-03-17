from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api import deps
from app.models.models import Business, User
from app.schemas.business import BusinessCreate, BusinessUpdate, Business as BusinessSchema

router = APIRouter()


class EscalationConfig(BaseModel):
    """Schema for escalation contact configuration"""
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_email: Optional[str] = Field(None, max_length=255)
    fallback_contact_name: Optional[str] = Field(None, max_length=255)
    fallback_contact_phone: Optional[str] = Field(None, max_length=20)
    fallback_contact_email: Optional[str] = Field(None, max_length=255)
    escalation_settings: Optional[dict] = Field(
        None,
        description="Settings: notify_via_sms, notify_via_push, notify_via_email, fallback_timeout_seconds"
    )


@router.get("", response_model=List[BusinessSchema])
def read_businesses(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve businesses.
    """
    if current_user.role == "admin":
        businesses = db.query(Business).offset(skip).limit(limit).all()
    else:
        businesses = db.query(Business).filter(Business.user_id == current_user.id).offset(skip).limit(limit).all()
    return businesses

@router.post("", response_model=BusinessSchema)
def create_business(
    *,
    db: Session = Depends(deps.get_db),
    business_in: BusinessCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new business.
    """
    business = Business(
        **business_in.model_dump(),
        user_id=current_user.id
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business

@router.get("/{id}", response_model=BusinessSchema)
def read_business(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get business by ID.
    """
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role != "admin" and business.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return business

@router.put("/{id}", response_model=BusinessSchema)
def update_business(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    business_update: BusinessUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a business.
    """
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role != "admin" and business.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    for field, value in business_update.model_dump(exclude_unset=True).items():
        setattr(business, field, value)
    
    db.commit()
    db.refresh(business)
    return business


@router.get("/{id}/escalation-config", response_model=EscalationConfig)
def get_escalation_config(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get escalation contact configuration for a business.
    """
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role != "admin" and business.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    return EscalationConfig(
        emergency_contact_name=business.emergency_contact_name,
        emergency_contact_phone=business.emergency_contact_phone,
        emergency_contact_email=business.emergency_contact_email,
        fallback_contact_name=business.fallback_contact_name,
        fallback_contact_phone=business.fallback_contact_phone,
        fallback_contact_email=business.fallback_contact_email,
        escalation_settings=business.escalation_settings
    )


@router.put("/{id}/escalation-config", response_model=EscalationConfig)
def update_escalation_config(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    config: EscalationConfig,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update escalation contact configuration for a business.
    
    This configures who gets notified when an escalation is triggered:
    - Emergency contact: Primary contact for urgent escalations (911 situations, emergencies)
    - Fallback contact: Secondary contact if primary is unavailable
    
    Escalation settings options:
    - notify_via_sms: bool - Send SMS notification
    - notify_via_push: bool - Send push notification to mobile app
    - notify_via_email: bool - Send email notification
    - fallback_timeout_seconds: int - Time before trying fallback contact (default: 300)
    """
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role != "admin" and business.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    # Update escalation fields
    business.emergency_contact_name = config.emergency_contact_name
    business.emergency_contact_phone = config.emergency_contact_phone
    business.emergency_contact_email = config.emergency_contact_email
    business.fallback_contact_name = config.fallback_contact_name
    business.fallback_contact_phone = config.fallback_contact_phone
    business.fallback_contact_email = config.fallback_contact_email
    business.escalation_settings = config.escalation_settings
    
    db.commit()
    db.refresh(business)
    
    return config
