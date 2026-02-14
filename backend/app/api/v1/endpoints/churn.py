"""
Customer Churn Prediction API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api import deps
from app.services.churn_service import churn_service


router = APIRouter()


class ChurnCalculateRequest(BaseModel):
    customer_phone: str


@router.post("/calculate")
async def calculate_churn_risk(
    request: ChurnCalculateRequest,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    result = churn_service.calculate_churn_risk(db, request.customer_phone, business_id)
    return result


@router.get("/at-risk")
async def get_at_risk_customers(
    min_score: int = 40,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    customers = churn_service.get_at_risk_customers(db, business_id, min_score)
    return {"at_risk_customers": customers}


@router.get("/stats")
async def get_churn_stats(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    stats = churn_service.get_churn_stats(db, business_id)
    return stats
