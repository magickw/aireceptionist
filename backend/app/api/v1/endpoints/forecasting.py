"""
Forecasting API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.api import deps
from app.services.forecasting_service import forecasting_service


router = APIRouter()


@router.get("/history")
async def get_call_history(
    days: int = 30,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    history = forecasting_service.get_call_volume_history(db, business_id, days)
    return {"history": history}


@router.get("/predict")
async def get_predictions(
    days_ahead: int = 7,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    predictions = forecasting_service.predict_daily_volume(db, business_id, days_ahead)
    return {"predictions": predictions}


@router.get("/weekly")
async def get_weekly_forecast(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    summary = forecasting_service.get_weekly_forecast_summary(db, business_id)
    return summary


@router.get("/peak-hours")
async def get_peak_hours(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    peak_hours = forecasting_service.get_peak_hours(db, business_id)
    return {"peak_hours": peak_hours}
