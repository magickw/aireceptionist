"""
Customer Intelligence API Endpoints

Provides endpoints for:
- Churn risk analysis
- VIP customer identification
- Semantic search across customer history
- Complaint pattern detection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.services.customer_intelligence import customer_intelligence_service


router = APIRouter()


@router.get("/churn-risk/{customer_phone}")
async def get_churn_risk(
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Calculate churn risk for a specific customer
    
    Returns churn risk score (0-1), risk level, contributing factors,
    and actionable recommendations
    """
    try:
        result = await customer_intelligence_service.calculate_churn_risk(
            customer_phone=customer_phone,
            business_id=business_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vip-customers")
async def get_vip_customers(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    min_satisfaction: Optional[float] = 4.5,
    min_appointments: Optional[int] = 5
):
    """
    Identify VIP customers based on multiple criteria
    
    Returns list of VIP customers with their metrics and VIP tier
    """
    try:
        result = await customer_intelligence_service.identify_vip_customers(
            business_id=business_id,
            db=db,
            min_satisfaction=min_satisfaction,
            min_appointments=min_appointments
        )
        return {
            "total_vip_customers": len(result),
            "customers": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic-search")
async def semantic_search_history(
    query: str,
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    top_k: Optional[int] = 5
):
    """
    Semantic search across customer interaction history
    
    Search for similar interactions using natural language queries
    """
    try:
        results = await customer_intelligence_service.semantic_search_customer_history(
            query=query,
            customer_phone=customer_phone,
            business_id=business_id,
            db=db,
            top_k=top_k
        )
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaint-patterns")
async def get_complaint_patterns(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    days: Optional[int] = 90
):
    """
    Detect patterns in customer complaints
    
    Analyzes common complaint topics, trending issues, and provides recommendations
    """
    try:
        result = await customer_intelligence_service.detect_complaint_patterns(
            business_id=business_id,
            db=db,
            days=days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index-customer/{customer_phone}")
async def index_customer_history(
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Index customer interaction history for semantic search
    
    Generates embeddings for all customer interactions
    """
    try:
        result = await customer_intelligence_service.index_customer_history(
            customer_phone=customer_phone,
            business_id=business_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))