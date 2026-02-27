"""
Reporting Service - Advanced Analytics and Reporting
Provides custom report generation and data export
"""

from datetime import datetime, timedelta, timezone
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
            end_date = datetime.now(timezone.utc) - timedelta(weeks=week)
            start_date = end_date - timedelta(weeks=1)
            
            metrics = self.get_call_metrics(db, business_id, start_date, end_date)
            summaries.append({
                "week_start": start_date.isoformat(),
                "week_end": end_date.isoformat(),
                "total_calls": metrics["total_calls"],
                "completion_rate": metrics["completion_rate"]
            })
        
        return summaries

    def calculate_roi_metrics(
        self,
        db: Session,
        business_id: int,
        start_date: datetime,
        end_date: datetime,
        avg_hourly_wage: float = 25.0
    ) -> Dict:
        """
        Calculate Return on Investment (ROI) metrics.
        Quantifies human hours saved and revenue captured by AI.
        """
        from app.models.models import CallSession, Order, Appointment
        
        # 1. Human Hours Saved (total call duration)
        total_seconds = db.query(func.sum(CallSession.duration_seconds)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.started_at <= end_date
        ).scalar() or 0
        
        hours_saved = total_seconds / 3600.0
        cost_savings = hours_saved * avg_hourly_wage
        
        # 2. Revenue Captured (Orders)
        order_revenue = db.query(func.sum(Order.total_amount)).filter(
            Order.business_id == business_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status.in_(["confirmed", "completed"])
        ).scalar() or 0
        
        # 3. Revenue Opportunity (Appointments - estimated value)
        # Assume an average appointment value of $50 if not specified
        appt_count = db.query(func.count(Appointment.id)).filter(
            Appointment.business_id == business_id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date,
            Appointment.status != "cancelled"
        ).scalar() or 0
        
        estimated_appt_revenue = appt_count * 50.0
        
        return {
            "human_hours_saved": round(hours_saved, 2),
            "cost_savings": round(float(cost_savings), 2),
            "revenue_captured": round(float(order_revenue), 2),
            "appointment_opportunity": round(float(estimated_appt_revenue), 2),
            "total_value_generated": round(float(cost_savings + float(order_revenue) + estimated_appt_revenue), 2),
            "avg_hourly_wage_baseline": avg_hourly_wage
        }
    
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
            end_date = datetime.now(timezone.utc)
        
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

    def get_realtime_stats(self, db: Session, business_id: int) -> Dict:
        """Get real-time statistics for the dashboard"""
        from app.models.models import CallSession
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today's stats
        calls_today = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= today_start
        ).scalar() or 0
        
        completed_today = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= today_start,
            CallSession.status == "ended"
        ).scalar() or 0
        
        # Active calls (started in last 30 mins and not ended)
        active_calls = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= now - timedelta(minutes=30),
            CallSession.ended_at.is_(None)
        ).scalar() or 0
        
        # Recent calls
        recent_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id
        ).order_by(desc(CallSession.started_at)).limit(5).all()
        
        return {
            "todayStats": {
                "calls_today": calls_today,
                "completed_calls": completed_today,
                "missed_calls": max(0, calls_today - completed_today),
                "avg_duration_today": 120.5  # Simulated for now
            },
            "activeCalls": active_calls,
            "recentCalls": [
                {
                    "id": c.id,
                    "customer_name": c.customer_name or "Unknown",
                    "customer_phone": c.customer_phone,
                    "status": c.status,
                    "started_at": c.started_at.isoformat() if c.started_at else None,
                    "duration": c.duration_seconds or 0
                }
                for c in recent_calls
            ]
        }


reporting_service = ReportingService()
