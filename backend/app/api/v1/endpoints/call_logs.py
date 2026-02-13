from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import CallSession, User, Business
from app.schemas.call_session import CallSession as CallSessionSchema

router = APIRouter()

@router.get("/", response_model=List[CallSessionSchema])
def read_call_logs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    business_id: int = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve call logs.
    """
    query = db.query(CallSession)
    
    if current_user.role != "admin":
        # Ensure user owns the business
        user_businesses = db.query(Business.id).filter(Business.user_id == current_user.id).all()
        business_ids = [b.id for b in user_businesses]
        if business_id:
            if business_id not in business_ids:
                 raise HTTPException(status_code=400, detail="Not enough permissions")
            query = query.filter(CallSession.business_id == business_id)
        else:
             query = query.filter(CallSession.business_id.in_(business_ids))
    elif business_id:
        query = query.filter(CallSession.business_id == business_id)

    call_sessions = query.order_by(CallSession.started_at.desc()).offset(skip).limit(limit).all()
    return call_sessions

@router.get("/{id}", response_model=CallSessionSchema)
def read_call_log(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get call log by ID.
    """
    call_session = db.query(CallSession).filter(CallSession.id == id).first()
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Permission check
    if current_user.role != "admin":
        business = db.query(Business).filter(Business.id == call_session.business_id).first()
        if not business or business.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Not enough permissions")
            
    return call_session
