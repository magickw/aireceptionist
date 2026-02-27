from typing import Any, Optional, Dict
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.services.reporting_service import reporting_service
from app.models.models import User

router = APIRouter()

@router.get("/roi", response_model=Dict[str, Any])
async def get_roi_analytics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    business_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365)
) -> Any:
    """
    Get ROI analytics for a business.
    """
    if not business_id:
        # Get first business of the user
        if not current_user.businesses:
            raise HTTPException(status_code=404, detail="No business found for user")
        business_id = current_user.businesses[0].id
    
    # Check permissions
    if current_user.role != "admin":
        is_owner = any(b.id == business_id for b in current_user.businesses)
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    return reporting_service.calculate_roi_metrics(
        db=db,
        business_id=business_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/summary", response_model=Dict[str, Any])
async def get_comprehensive_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    business_id: Optional[int] = None,
    report_type: str = Query("weekly", regex="^(daily|weekly|monthly)$")
) -> Any:
    """
    Get a comprehensive analytics report.
    """
    if not business_id:
        if not current_user.businesses:
            raise HTTPException(status_code=404, detail="No business found for user")
        business_id = current_user.businesses[0].id
        
    return reporting_service.generate_report(
        db=db,
        business_id=business_id,
        report_type=report_type
    )

@router.get("/business/{business_id}", response_model=Dict[str, Any])
async def get_business_analytics(
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    days: int = Query(30, ge=1, le=365)
) -> Any:
    """
    Get comprehensive analytics for a specific business.
    """
    # Check permissions
    if current_user.role != "admin":
        is_owner = any(b.id == business_id for b in current_user.businesses)
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    return reporting_service.generate_report(
        db=db,
        business_id=business_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/business/{business_id}/realtime", response_model=Dict[str, Any])
async def get_business_realtime_analytics(
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get real-time analytics for a specific business.
    """
    # Check permissions
    if current_user.role != "admin":
        is_owner = any(b.id == business_id for b in current_user.businesses)
        if not is_owner:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return reporting_service.get_realtime_stats(db=db, business_id=business_id)
