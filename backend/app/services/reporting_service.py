"""
Reporting Service - Advanced Analytics and Reporting
Provides custom report generation and data export
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import json


class ReportingService:
    """Service for advanced reporting and analytics"""
    
    def get_call_metrics(
        self,
        db: Session,
        business_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get comprehensive call metrics"""
        from app.models.models import CallSession
        
        # Total calls
        total_calls = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date
        ).scalar()
        
        # Completed calls
        completed_calls = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date,
            CallSession.status == "ended"
        ).scalar()
        
        # Missed calls
        missed_calls = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date,
            CallSession.status == "missed"
        ).scalar()
        
        # Average duration
        avg_duration = db.query(func.avg(
            func.extract('epoch', CallSession.ended_at) - func.extract('epoch', CallSession.started_at))
        ).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date,
            CallSession.ended_at.isnot(None)
        ).scalar()
        
        return {
            "total_calls": total_calls or 0,
            "completed_calls": completed_calls or 0,
            "missed_calls": missed_calls or 0,
            "completion_rate": round((completed_calls or 0) / max(total_calls or 1, 1) * 100, 1),
            "average_duration_seconds": round(avg_duration or 0, 1)
        }
    
    def get_customer_metrics(
        self,
        db: Session,
        business_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get customer-related metrics"""
        from app.models.models import CallSession
        
        # Unique customers
        unique_customers = db.query(
            func.count(func.distinct(CallSession.customer_phone))
        ).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date,
            CallSession.customer_phone.isnot(None)
        ).scalar()
        
        # New vs returning
        returning_customers = db.query(func.count(CallSession.customer_phone)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date,
            CallSession.customer_phone.in_(
                db.query(CallSession.customer_phone).filter(
                    CallSession.business_id == business_id,
                    CallSession.started_at < start_date
                )
            )
        ).scalar() or 0
        
        return {
            "unique_customers": unique_customers or 0,
            "returning_customers": returning_customers,
            "new_customers": max((unique_customers or 0) - returning_customers, 0)
        }
    
    def get_hourly_distribution(
        self,
        db: Session,
        business_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get hourly call distribution"""
        from app.models.models import CallSession
        
        results = db.query(
            func.extract('hour', CallSession.started_at).label('hour'),
            func.count(CallSession.id).label('count')
        ).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date
        ).group_by(
            func.extract('hour', CallSession.started_at)
        ).order_by(
            func.extract('hour', CallSession.started_at)
        ).all()
        
        # Fill in missing hours
        hourly_data = {int(r.hour): r.count for r in results}
        return [{"hour": h, "count": hourly_data.get(h, 0)} for h in range(24)]
    
    def get_weekly_summary(
        self,
        db: Session,
        business_id: int,
        weeks: int = 4
    ) -> List[Dict]:
        """Get weekly summary for past N weeks"""
        summaries = []
        
        for week in range(weeks):
            end_date = datetime.utcnow() - timedelta(weeks=week)
            start_date = end_date - timedelta(weeks=1)
            
            metrics = self.get_call_metrics(db, business_id, start_date, end_date)
            summaries.append({
                "week_start": start_date.isoformat(),
                "week_end": end_date.isoformat(),
                "total_calls": metrics["total_calls"],
                "completion_rate": metrics["completion_rate"]
            })
        
        return summaries
    
    def export_to_csv(
        self,
        db: Session,
        business_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Export call data to CSV format"""
        from app.models.models import CallSession
        
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date
        ).all()
        
        csv_lines = ["ID,Customer,Phone,Start Time,End Time,Status,Duration"]
        
        for call in calls:
            duration = ""
            if call.started_at and call.ended_at:
                duration = str(int((call.ended_at - call.started_at).total_seconds()))
            
            customer_name = call.customer_name or ''
            csv_lines.append(
                f"{call.id},"
                f'"{customer_name}",'
                f"{call.customer_phone or ''},"
                f"{call.started_at or ''},"
                f"{call.ended_at or ''},"
                f"{call.status or ''},"
                f"{duration}"
            )
        
        return "\n".join(csv_lines)
    
    def generate_report(
        self,
        db: Session,
        business_id: int,
        report_type: str = "weekly",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Generate a comprehensive report"""
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            if report_type == "daily":
                start_date = end_date - timedelta(days=1)
            elif report_type == "weekly":
                start_date = end_date - timedelta(weeks=1)
            elif report_type == "monthly":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(weeks=1)
        
        return {
            "report_type": report_type,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "call_metrics": self.get_call_metrics(db, business_id, start_date, end_date),
            "customer_metrics": self.get_customer_metrics(db, business_id, start_date, end_date),
            "hourly_distribution": self.get_hourly_distribution(db, business_id, start_date, end_date),
            "weekly_summary": self.get_weekly_summary(db, business_id, 4) if report_type == "monthly" else []
        }


reporting_service = ReportingService()
