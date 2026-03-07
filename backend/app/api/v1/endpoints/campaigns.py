from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import User
from app.services.outbound_campaign_service import OutboundCampaignService

router = APIRouter()


class CampaignCreate(BaseModel):
    business_id: int
    name: str
    campaign_type: str  # appointment_reminder, follow_up, re_engagement, custom
    briefing: str = ""
    target_criteria: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    max_concurrent_calls: int = 3
    max_retries: int = 2


def _check_business_permission(current_user: User, business_id: int):
    if current_user.role != "admin":
        is_owner = any(b.id == business_id for b in current_user.businesses)
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not enough permissions")


@router.post("", response_model=Dict[str, Any])
async def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new outbound campaign."""
    _check_business_permission(current_user, payload.business_id)
    service = OutboundCampaignService(db)
    return await service.create_campaign(
        business_id=payload.business_id,
        name=payload.name,
        campaign_type=payload.campaign_type,
        briefing=payload.briefing,
        target_criteria=payload.target_criteria,
        schedule=payload.schedule,
        max_concurrent=payload.max_concurrent_calls,
        max_retries=payload.max_retries,
    )


@router.get("/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get campaign details with call statistics."""
    service = OutboundCampaignService(db)
    result = await service.get_campaign_details(campaign_id)
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _check_business_permission(current_user, result["business_id"])
    return result


@router.get("", response_model=List[Dict[str, Any]])
async def list_campaigns(
    business_id: int = Query(...),
    status: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """List campaigns for a business."""
    _check_business_permission(current_user, business_id)
    from app.models.models import Campaign
    query = db.query(Campaign).filter(Campaign.business_id == business_id)
    if status:
        query = query.filter(Campaign.status == status)
    campaigns = query.order_by(Campaign.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "campaign_type": c.campaign_type,
            "status": c.status,
            "total_targets": c.total_targets,
            "calls_made": c.calls_made,
            "calls_answered": c.calls_answered,
            "calls_successful": c.calls_successful,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
        }
        for c in campaigns
    ]


@router.post("/{campaign_id}/start", response_model=Dict[str, Any])
async def start_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Start a campaign."""
    service = OutboundCampaignService(db)
    details = await service.get_campaign_details(campaign_id)
    if not details:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _check_business_permission(current_user, details["business_id"])
    return await service.start_campaign(campaign_id)


@router.post("/{campaign_id}/pause", response_model=Dict[str, Any])
async def pause_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Pause a running campaign."""
    service = OutboundCampaignService(db)
    details = await service.get_campaign_details(campaign_id)
    if not details:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _check_business_permission(current_user, details["business_id"])
    return await service.pause_campaign(campaign_id)


@router.post("/{campaign_id}/cancel", response_model=Dict[str, Any])
async def cancel_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Cancel a campaign."""
    service = OutboundCampaignService(db)
    details = await service.get_campaign_details(campaign_id)
    if not details:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _check_business_permission(current_user, details["business_id"])
    return await service.cancel_campaign(campaign_id)


@router.get("/{campaign_id}/calls", response_model=List[Dict[str, Any]])
async def get_campaign_calls(
    campaign_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get calls for a campaign."""
    service = OutboundCampaignService(db)
    details = await service.get_campaign_details(campaign_id)
    if not details:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _check_business_permission(current_user, details["business_id"])

    from app.models.models import CampaignCall, Customer
    query = db.query(CampaignCall).filter(CampaignCall.campaign_id == campaign_id)
    if status:
        query = query.filter(CampaignCall.status == status)
    calls = query.order_by(CampaignCall.created_at.desc()).all()
    result = []
    for cc in calls:
        customer = db.query(Customer).filter(Customer.id == cc.customer_id).first()
        result.append({
            "id": cc.id,
            "customer_id": cc.customer_id,
            "customer_name": customer.name if customer else None,
            "customer_phone": customer.phone if customer else None,
            "status": cc.status,
            "attempt_number": cc.attempt_number,
            "outcome": cc.outcome,
            "outcome_details": cc.outcome_details,
            "call_duration_seconds": cc.call_duration_seconds,
            "called_at": cc.called_at.isoformat() if cc.called_at else None,
        })
    return result


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_stats(
    business_id: int = Query(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get outbound campaign statistics."""
    _check_business_permission(current_user, business_id)
    service = OutboundCampaignService(db)
    return await service.get_outbound_stats(business_id)


@router.post("/trigger-reminders", response_model=Dict[str, Any])
async def trigger_reminders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    business_id: int = Body(..., embed=True),
) -> Any:
    """Trigger AI reminder calls for upcoming appointments."""
    _check_business_permission(current_user, business_id)
    service = OutboundCampaignService(db)
    return await service.trigger_appointment_reminders(business_id)
