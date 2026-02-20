"""
Smart Scheduling API Endpoints
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.services.smart_scheduling_service import smart_scheduling_service


router = APIRouter()


class NoShowPredictionRequest(BaseModel):
    customer_phone: str
    appointment_time: datetime
    service_type: Optional[str] = None


class OptimalTimeRequest(BaseModel):
    customer_phone: str
    preferred_date: datetime
    service_duration_minutes: int = 60
    max_suggestions: int = 5


@router.post("/no-show-prediction")
async def predict_no_show(
    request: NoShowPredictionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Predict no-show probability for an appointment"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await smart_scheduling_service.predict_no_show_probability(
        db, business_id, request.customer_phone, 
        request.appointment_time, request.service_type
    )
    return result


@router.post("/suggest-times")
async def suggest_optimal_times(
    request: OptimalTimeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get optimal appointment time suggestions"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await smart_scheduling_service.suggest_optimal_times(
        db, business_id, request.customer_phone,
        request.preferred_date, request.service_duration_minutes,
        request.max_suggestions
    )
    return result


@router.get("/analytics")
async def get_scheduling_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get scheduling analytics and insights"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await smart_scheduling_service.get_scheduling_analytics(db, business_id, days)
    return result


@router.post("/reminder/{appointment_id}")
async def send_appointment_reminder(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send appointment reminder to customer"""
    result = await smart_scheduling_service.send_appointment_reminder(db, appointment_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
