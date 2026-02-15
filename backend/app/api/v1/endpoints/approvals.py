"""
Approval Management API
Handles manager approval requests for AI actions requiring review
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.models import ApprovalRequest, User, CallSession

router = APIRouter()


@router.post("/request")
def create_approval_request(
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
    approval = ApprovalRequest(
        business_id=current_user.businesses[0].id,
        call_session_id=call_session_id,
        request_type=request_type,
        status="pending",
        reason=reason,
        original_response=original_response,
        context=context,
        request_request_metadata={"created_by": current_user.email}
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/override")
def approve_override(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request_type: str,
    call_session_id: str,
    original_response: str,
    context: Dict[str, Any],
    notes: str = ""
) -> Any:
    """Approve an AI override request"""
    # Create or update approval request
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.call_session_id == call_session_id,
        ApprovalRequest.request_type == request_type,
        ApprovalRequest.status == "pending"
    ).first()
    
    if not approval:
        approval = ApprovalRequest(
            business_id=current_user.businesses[0].id,
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
        approval.metadata = {"manager_notes": notes}
    
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/reject")
def reject_request(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request_type: str,
    call_session_id: str,
    context: Dict[str, Any],
    notes: str = ""
) -> Any:
    """Reject an AI action request"""
    # Create or update approval request
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.call_session_id == call_session_id,
        ApprovalRequest.request_type == request_type,
        ApprovalRequest.status == "pending"
    ).first()
    
    if not approval:
        approval = ApprovalRequest(
            business_id=current_user.businesses[0].id,
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
        approval.metadata = {"manager_notes": notes}
    
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/")
def list_pending_approvals(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50
) -> Any:
    """List pending approval requests"""
    query = db.query(ApprovalRequest).filter(
        ApprovalRequest.business_id == current_user.businesses[0].id,
        ApprovalRequest.status == "pending"
    ).order_by(ApprovalRequest.created_at.desc()).offset(skip).limit(limit)
    
    return query.all()


@router.get("/{approval_id}")
def get_approval(
    approval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific approval request"""
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.business_id == current_user.businesses[0].id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return approval


@router.get("/history")
def get_approval_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    limit: int = 50
) -> Any:
    """Get approval history"""
    approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.business_id == current_user.businesses[0].id
    ).order_by(ApprovalRequest.created_at.desc()).limit(limit).all()
    
    return approvals
