"""
Customer 360 API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.services.customer_360_service import customer_360_service


router = APIRouter()


@router.get("/profile/{phone}")
async def get_customer_profile(
    phone: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get complete 360-degree view of a customer"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await customer_360_service.get_customer_profile(db, business_id, phone)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/top")
async def get_top_customers(
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("lifetime_value", regex="^(lifetime_value|total_spent|total_orders)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get top customers by various metrics"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await customer_360_service.get_top_customers(db, business_id, limit, sort_by)
    return {"customers": result}


@router.get("/segments")
async def get_customer_segments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get customer segments for targeted marketing"""
    business_id = current_user.businesses[0].id if current_user.businesses else None
    if not business_id:
        raise HTTPException(status_code=400, detail="No business associated with user")
    
    result = await customer_360_service.get_customer_segments(db, business_id)
    return result


@router.post("/update-metrics/{customer_id}")
async def update_customer_metrics(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Recalculate all customer metrics"""
    result = await customer_360_service.update_customer_metrics(db, customer_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
