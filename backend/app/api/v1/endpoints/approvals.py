"""
Approval Management API
Handles manager approval requests for AI actions requiring review
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app.api import deps
from app.models.models import ApprovalRequest, User, CallSession


# Pydantic schemas for validation
class OverrideRequest(BaseModel):
    request_type: Optional[str] = None
    call_session_id: Optional[str] = None
    original_response: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    notes: Optional[str] = ""


class RejectRequest(BaseModel):
    request_type: Optional[str] = None
    call_session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    notes: Optional[str] = ""


router = APIRouter()


@router.post("/request")
async def create_approval_request(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request_type: str,
    call_session_id: str,
    reason: str,
    original_response: str,
    context: Dict[str, Any],
) -> Any:
    """Create a new approval request"""
    business_id = await deps.get_current_business_id(current_user, db)
    approval = ApprovalRequest(
        business_id=business_id,
        call_session_id=call_session_id,
        request_type=request_type,
        status="pending",
        reason=reason,
        original_response=original_response,
        context=context,
        request_metadata={"created_by": current_user.email}
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/override")
async def approve_override(
    request: OverrideRequest,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Approve an AI override request"""
    business_id = await deps.get_current_business_id(current_user, db)
    
    # Use provided values or defaults
    call_session_id = request.call_session_id or "unknown"
    request_type = request.request_type or "override"
    original_response = request.original_response or ""
    context = request.context or {}
    notes = request.notes or ""
    
    # Create or update approval request
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.call_session_id == call_session_id,
        ApprovalRequest.request_type == request_type,
        ApprovalRequest.status == "pending"
    ).first()
    
    if not approval:
        approval = ApprovalRequest(
            business_id=business_id,
            call_session_id=call_session_id,
            request_type=request_type,
            status="approved",
            action_taken="APPROVED_OVERRIDE",
            reason="Manager override",
            original_response=original_response,
            final_response=original_response,
            context=context,
            reviewed_by=current_user.id,
            reviewed_at=datetime.utcnow(),
            request_metadata={"manager_notes": notes}
        )
        db.add(approval)
    else:
        approval.status = "approved"
        approval.action_taken = "APPROVED_OVERRIDE"
        approval.final_response = original_response
        approval.reviewed_by = current_user.id
        approval.reviewed_at = datetime.utcnow()
        approval.request_metadata = {"manager_notes": notes}
    
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/reject")
async def reject_request(
    request: RejectRequest,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Reject an AI action request"""
    business_id = await deps.get_current_business_id(current_user, db)
    
    # Use provided values or defaults
    call_session_id = request.call_session_id or "unknown"
    request_type = request.request_type or "unknown"
    context = request.context or {}
    notes = request.notes or ""
    
    # Create or update approval request
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.call_session_id == call_session_id,
        ApprovalRequest.request_type == request_type,
        ApprovalRequest.status == "pending"
    ).first()
    
    if not approval:
        approval = ApprovalRequest(
            business_id=business_id,
            call_session_id=call_session_id,
            request_type=request_type,
            status="rejected",
            action_taken="REJECTED",
            reason="Manager rejected",
            original_response="",
            final_response=context.get("suggested_response", ""),
            context=context,
            reviewed_by=current_user.id,
            reviewed_at=datetime.utcnow(),
            request_metadata={"manager_notes": notes}
        )
        db.add(approval)
    else:
        approval.status = "rejected"
        approval.action_taken = "REJECTED"
        approval.reviewed_by = current_user.id
        approval.reviewed_at = datetime.utcnow()
        approval.request_metadata = {"manager_notes": notes}
    
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/")
async def list_pending_approvals(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50
) -> Any:
    """List pending approval requests"""
    business_id = await deps.get_current_business_id(current_user, db)
    query = db.query(ApprovalRequest).filter(
        ApprovalRequest.business_id == business_id,
        ApprovalRequest.status == "pending"
    ).order_by(ApprovalRequest.created_at.desc()).offset(skip).limit(limit)
    
    return query.all()


@router.get("/{approval_id}")
async def get_approval(
    approval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific approval request"""
    business_id = await deps.get_current_business_id(current_user, db)
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.business_id == business_id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return approval


@router.get("/history")
async def get_approval_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    limit: int = 50
) -> Any:
    """Get approval history"""
    business_id = await deps.get_current_business_id(current_user, db)
    approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.business_id == business_id
    ).order_by(ApprovalRequest.created_at.desc()).limit(limit).all()
    
    return approvals
