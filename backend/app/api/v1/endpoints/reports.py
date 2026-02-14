"""
Reporting API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.api import deps
from app.services.reporting_service import reporting_service


router = APIRouter()


@router.get("/metrics")
async def get_call_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    end_dt = datetime.utcnow() if not end_date else datetime.fromisoformat(end_date)
    start_dt = end_dt - timedelta(days=7) if not start_date else datetime.fromisoformat(start_date)
    
    metrics = reporting_service.get_call_metrics(db, business_id, start_dt, end_dt)
    return metrics


@router.get("/customers")
async def get_customer_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    end_dt = datetime.utcnow() if not end_date else datetime.fromisoformat(end_date)
    start_dt = end_dt - timedelta(days=7) if not start_date else datetime.fromisoformat(start_date)
    
    metrics = reporting_service.get_customer_metrics(db, business_id, start_dt, end_dt)
    return metrics


@router.get("/hourly")
async def get_hourly_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    end_dt = datetime.utcnow() if not end_date else datetime.fromisoformat(end_date)
    start_dt = end_dt - timedelta(days=7) if not start_date else datetime.fromisoformat(start_date)
    
    distribution = reporting_service.get_hourly_distribution(db, business_id, start_dt, end_dt)
    return {"hourly_distribution": distribution}


@router.get("/weekly")
async def get_weekly_summary(
    weeks: int = 4,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    summary = reporting_service.get_weekly_summary(db, business_id, weeks)
    return {"weekly_summary": summary}


@router.get("/generate")
async def generate_report(
    report_type: str = Query("weekly", enum=["daily", "weekly", "monthly"]),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    report = reporting_service.generate_report(
        db, business_id, report_type, start_dt, end_dt
    )
    return report


@router.get("/export")
async def export_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    end_dt = datetime.utcnow() if not end_date else datetime.fromisoformat(end_date)
    start_dt = end_dt - timedelta(days=7) if not start_date else datetime.fromisoformat(start_date)
    
    csv_data = reporting_service.export_to_csv(db, business_id, start_dt, end_dt)
    
    return {
        "filename": f"calls_export_{start_dt.date()}_{end_dt.date()}.csv",
        "data": csv_data
    }
