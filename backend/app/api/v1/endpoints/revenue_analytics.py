"""
Revenue Analytics API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.services.revenue_analytics_service import revenue_analytics_service


router = APIRouter()


@router.get("/dashboard")
async def get_revenue_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get comprehensive revenue dashboard metrics"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await revenue_analytics_service.get_revenue_dashboard(db, business_id, days)
    return result


@router.get("/forecast")
async def get_revenue_forecast(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get revenue forecast for upcoming days"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await revenue_analytics_service.get_revenue_forecast(db, business_id, days)
    return result
