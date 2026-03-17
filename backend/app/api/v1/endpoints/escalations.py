"""
Escalation Management Endpoints

API endpoints for managing escalations:
- List pending escalations
- Acknowledge escalation
- Resolve escalation
- Escalate to fallback
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.api import deps
from app.models.models import Escalation, User, Business
from app.services.escalation_service import escalation_service, EscalationState, EscalationLevel

router = APIRouter()


class EscalationResponse(BaseModel):
    """Schema for escalation response"""
    id: int
    business_id: int
    business_name: Optional[str] = None
    call_session_id: Optional[str] = None
    state: str
    trigger_type: str
    severity: str
    reason: str
    context: Optional[dict] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    sla_breached: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_action: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EscalationListResponse(BaseModel):
    """Schema for escalation list with metadata"""
    total: int
    escalations: List[EscalationResponse]
    sla_breached_count: int
    by_severity: dict


class AcknowledgeRequest(BaseModel):
    """Request body for acknowledging an escalation"""
    notes: Optional[str] = Field(None, description="Optional notes about the acknowledgment")


class ResolveRequest(BaseModel):
    """Request body for resolving an escalation"""
    resolution_action: str = Field(..., description="Action taken: callback, transfer, handled_by_ai, dismissed")
    notes: Optional[str] = Field(None, description="Optional notes about the resolution")


@router.get("", response_model=EscalationListResponse)
def list_escalations(
    db: Session = Depends(deps.get_db),
    state: Optional[str] = Query(None, description="Filter by state: triggered, notified, acknowledged, resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, emergency"),
    business_id: Optional[int] = Query(None, description="Filter by business ID"),
    sla_breached: Optional[bool] = Query(None, description="Filter by SLA breach status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    List escalations for supervisor dashboard.
    
    - By default, shows non-resolved escalations
    - Can filter by state, severity, business, SLA breach
    - Includes summary statistics
    """
    query = db.query(Escalation)
    
    # Filter by business access
    if current_user.role != "admin":
        user_businesses = [b.id for b in current_user.businesses]
        query = query.filter(Escalation.business_id.in_(user_businesses))
    
    # Apply filters
    if state:
        query = query.filter(Escalation.state == state)
    else:
        # Default: show non-resolved
        query = query.filter(Escalation.state != EscalationState.RESOLVED.value)
    
    if severity:
        query = query.filter(Escalation.severity == severity)
    
    if business_id:
        query = query.filter(Escalation.business_id == business_id)
    
    if sla_breached is not None:
        query = query.filter(Escalation.sla_breached == sla_breached)
    
    # Get totals
    total = query.count()
    sla_breached_count = query.filter(Escalation.sla_breached == True).count()
    
    # Get severity breakdown
    from sqlalchemy import func
    severity_counts = db.query(
        Escalation.severity,
        func.count(Escalation.id)
    ).filter(
        Escalation.state != EscalationState.RESOLVED.value
    ).group_by(Escalation.severity).all()
    
    by_severity = {s: c for s, c in severity_counts}
    
    # Get escalations with business name
    escalations = query.order_by(Escalation.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich with business name
    escalation_responses = []
    for esc in escalations:
        business = db.query(Business).filter(Business.id == esc.business_id).first()
        esc_dict = {
            "id": esc.id,
            "business_id": esc.business_id,
            "business_name": business.name if business else None,
            "call_session_id": esc.call_session_id,
            "state": esc.state,
            "trigger_type": esc.trigger_type,
            "severity": esc.severity,
            "reason": esc.reason,
            "context": esc.context,
            "customer_phone": esc.customer_phone,
            "customer_name": esc.customer_name,
            "sla_deadline": esc.sla_deadline,
            "sla_breached": esc.sla_breached,
            "acknowledged_by": esc.acknowledged_by,
            "acknowledged_at": esc.acknowledged_at,
            "resolved_by": esc.resolved_by,
            "resolved_at": esc.resolved_at,
            "resolution_action": esc.resolution_action,
            "created_at": esc.created_at,
            "updated_at": esc.updated_at,
        }
        escalation_responses.append(EscalationResponse(**esc_dict))
    
    return EscalationListResponse(
        total=total,
        escalations=escalation_responses,
        sla_breached_count=sla_breached_count,
        by_severity=by_severity
    )


@router.get("/{escalation_id}", response_model=EscalationResponse)
def get_escalation(
    escalation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """Get details of a specific escalation"""
    
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    # Check access
    if current_user.role != "admin":
        user_businesses = [b.id for b in current_user.businesses]
        if escalation.business_id not in user_businesses:
            raise HTTPException(status_code=403, detail="Access denied")
    
    business = db.query(Business).filter(Business.id == escalation.business_id).first()
    
    return EscalationResponse(
        id=escalation.id,
        business_id=escalation.business_id,
        business_name=business.name if business else None,
        call_session_id=escalation.call_session_id,
        state=escalation.state,
        trigger_type=escalation.trigger_type,
        severity=escalation.severity,
        reason=escalation.reason,
        context=escalation.context,
        customer_phone=escalation.customer_phone,
        customer_name=escalation.customer_name,
        sla_deadline=escalation.sla_deadline,
        sla_breached=escalation.sla_breached,
        acknowledged_by=escalation.acknowledged_by,
        acknowledged_at=escalation.acknowledged_at,
        resolved_by=escalation.resolved_by,
        resolved_at=escalation.resolved_at,
        resolution_action=escalation.resolution_action,
        created_at=escalation.created_at,
        updated_at=escalation.updated_at,
    )


@router.post("/{escalation_id}/acknowledge")
async def acknowledge_escalation(
    escalation_id: int,
    request: AcknowledgeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Acknowledge an escalation.
    
    This indicates that a human is aware of and working on the escalation.
    """
    
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    # Check access
    if current_user.role != "admin":
        user_businesses = [b.id for b in current_user.businesses]
        if escalation.business_id not in user_businesses:
            raise HTTPException(status_code=403, detail="Access denied")
    
    result = await escalation_service.acknowledge_escalation(
        db=db,
        escalation_id=escalation_id,
        acknowledged_by=current_user.id,
        notes=request.notes
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: int,
    request: ResolveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Resolve an escalation.
    
    Valid resolution actions:
    - callback: Called the customer back
    - transfer: Transferred to human agent
    - handled_by_ai: Let AI handle it after review
    - dismissed: Not a valid escalation
    """
    
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    # Check access
    if current_user.role != "admin":
        user_businesses = [b.id for b in current_user.businesses]
        if escalation.business_id not in user_businesses:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate resolution action
    valid_actions = ["callback", "transfer", "handled_by_ai", "dismissed"]
    if request.resolution_action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resolution action. Must be one of: {valid_actions}"
        )
    
    result = await escalation_service.resolve_escalation(
        db=db,
        escalation_id=escalation_id,
        resolved_by=current_user.id,
        resolution_action=request.resolution_action,
        notes=request.notes
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/{escalation_id}/escalate-fallback")
async def escalate_to_fallback(
    escalation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Manually escalate to fallback contact.
    
    Use this when the primary contact is unresponsive.
    """
    
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    # Check access
    if current_user.role != "admin":
        user_businesses = [b.id for b in current_user.businesses]
        if escalation.business_id not in user_businesses:
            raise HTTPException(status_code=403, detail="Access denied")
    
    result = await escalation_service.escalate_to_fallback(
        db=db,
        escalation_id=escalation_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/check-sla")
def check_sla_breaches(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Check for SLA breaches and mark them.
    
    This endpoint can be called by a cron job to automatically
    detect and flag SLA breaches.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    breached = escalation_service.check_sla_breaches(db)
    
    return {
        "success": True,
        "breaches_detected": len(breached),
        "breached_escalation_ids": [e.id for e in breached]
    }
