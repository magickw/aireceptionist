from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import User
from app.services.outbound_campaign_service import OutboundCampaignService

router = APIRouter()

@router.post("/trigger-reminders", response_model=Dict[str, Any])
async def trigger_reminders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    business_id: int = Body(..., embed=True)
) -> Any:
    """
    Trigger AI reminder calls for upcoming appointments.
    """
    # Permission check
    if current_user.role != "admin":
        is_owner = any(b.id == business_id for b in current_user.businesses)
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    service = OutboundCampaignService(db)
    return await service.trigger_appointment_reminders(business_id)

@router.post("/custom-outreach", response_model=Dict[str, Any])
async def create_outreach(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    business_id: int = Body(...),
    customer_ids: List[int] = Body(...),
    briefing: str = Body(...)
) -> Any:
    """
    Trigger a custom AI outreach campaign.
    """
    # Permission check
    if current_user.role != "admin":
        is_owner = any(b.id == business_id for b in current_user.businesses)
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    service = OutboundCampaignService(db)
    return await service.create_custom_campaign(business_id, customer_ids, briefing)

@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    business_id: int = None
) -> Any:
    if not business_id:
        if not current_user.businesses:
            raise HTTPException(status_code=404, detail="No business found")
        business_id = current_user.businesses[0].id
        
    service = OutboundCampaignService(db)
    return await service.get_outbound_stats(business_id)
