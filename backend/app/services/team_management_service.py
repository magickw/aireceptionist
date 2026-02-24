"""
Team Management Service
Staff scheduling, performance dashboards, and call distribution
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, time, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from decimal import Decimal
import json

from app.core.config import settings


class TeamManagementService:
    """Service for team management and performance tracking"""
    
    def __init__(self):
        pass
    
    def create_team_member(
        self,
        db: Session,
        business_id: int,
        name: str,
        email: str = None,
        phone: str = None,
        role: str = "staff",
        department: str = None
    ) -> Dict:
        """Create a new team member"""
        from app.models.models import TeamMember
        
        member = TeamMember(
            business_id=business_id,
            name=name,
            email=email,
            phone=phone,
            role=role,
            department=department
        )
        
        db.add(member)
        db.commit()
        db.refresh(member)
        
        return {
            "id": member.id,
            "name": member.name,
            "role": member.role,
            "status": member.status
        }
    
    def get_team_members(
        self,
        db: Session,
        business_id: int,
        department: str = None,
        status: str = None
    ) -> List[Dict]:
        """Get all team members for a business"""
        from app.models.models import TeamMember
        
        query = db.query(TeamMember).filter(TeamMember.business_id == business_id)
        
        if department:
            query = query.filter(TeamMember.department == department)
        
        if status:
            query = query.filter(TeamMember.status == status)
        
        members = query.all()
        
        return [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "phone": m.phone,
                "role": m.role,
                "department": m.department,
                "status": m.status,
                "calls_handled": m.calls_handled or 0,
                "avg_quality_score": float(m.avg_quality_score) if m.avg_quality_score else None,
                "is_available": self._is_member_available(m)
            }
            for m in members
        ]
    
    def _is_member_available(self, member) -> bool:
        """Check if team member is currently available"""
        if member.status != "active":
            return False
        
        if not member.weekly_hours:
            return True  # No schedule = always available
        
        now = datetime.now(timezone.utc)
        day_name = now.strftime('%A').lower()
        current_time = now.time()
        
        day_schedule = member.weekly_hours.get(day_name)
        if not day_schedule:
            return False  # Not scheduled today
        
        try:
            start_time = datetime.strptime(day_schedule.get('start', '09:00'), '%H:%M').time()
            end_time = datetime.strptime(day_schedule.get('end', '17:00'), '%H:%M').time()
            
            return start_time <= current_time <= end_time
        except:
            return True
    
    def update_member_schedule(
        self,
        db: Session,
        member_id: int,
        weekly_hours: Dict
    ) -> Dict:
        """Update team member's weekly schedule"""
        from app.models.models import TeamMember
        
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        
        if not member:
            return {"error": "Team member not found"}
        
        member.weekly_hours = weekly_hours
        db.commit()
        
        return {
            "id": member_id,
            "weekly_hours": weekly_hours
        }
    
    def get_team_performance(
        self,
        db: Session,
        business_id: int,
        days: int = 30
    ) -> Dict:
        """Get team performance metrics"""
        from app.models.models import TeamMember, CallSession
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        members = db.query(TeamMember).filter(
            TeamMember.business_id == business_id
        ).all()
        
        performance_data = []
        
        for member in members:
            # Get calls handled by this member (via transfer)
            # Note: This requires call_sessions to have a transferred_to field
            # For now, we'll use the member's stored metrics
            
            performance_data.append({
                "id": member.id,
                "name": member.name,
                "role": member.role,
                "calls_handled": member.calls_handled or 0,
                "avg_quality_score": float(member.avg_quality_score) if member.avg_quality_score else None,
                "avg_satisfaction": float(member.avg_satisfaction) if member.avg_satisfaction else None,
                "status": member.status
            })
        
        # Calculate team averages
        total_calls = sum(p["calls_handled"] for p in performance_data)
        avg_quality = sum(p["avg_quality_score"] or 0 for p in performance_data) / len(performance_data) if performance_data else 0
        
        return {
            "period_days": days,
            "team_size": len(members),
            "total_calls_handled": total_calls,
            "team_avg_quality": round(avg_quality, 1),
            "members": performance_data
        }
    
    def get_staff_schedule(
        self,
        db: Session,
        business_id: int,
        date: datetime = None
    ) -> Dict:
        """Get staff schedule for a specific date"""
        from app.models.models import TeamMember
        
        date = date or datetime.now(timezone.utc)
        day_name = date.strftime('%A').lower()
        
        members = db.query(TeamMember).filter(
            TeamMember.business_id == business_id,
            TeamMember.status == "active"
        ).all()
        
        schedule = []
        for member in members:
            if member.weekly_hours and day_name in member.weekly_hours:
                day_schedule = member.weekly_hours[day_name]
                schedule.append({
                    "member_id": member.id,
                    "name": member.name,
                    "start_time": day_schedule.get('start'),
                    "end_time": day_schedule.get('end'),
                    "department": member.department,
                    "role": member.role
                })
        
        # Sort by start time
        schedule.sort(key=lambda x: x.get('start_time', '00:00'))
        
        return {
            "date": date.strftime('%Y-%m-%d'),
            "day": day_name,
            "staff_on_duty": len(schedule),
            "schedule": schedule
        }
    
    def update_member_metrics(
        self,
        db: Session,
        member_id: int,
        quality_score: float = None,
        satisfaction: float = None
    ) -> Dict:
        """Update team member performance metrics"""
        from app.models.models import TeamMember
        
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        
        if not member:
            return {"error": "Team member not found"}
        
        member.calls_handled = (member.calls_handled or 0) + 1
        
        if quality_score is not None:
            # Calculate rolling average
            current_avg = float(member.avg_quality_score) if member.avg_quality_score else 0
            member.avg_quality_score = Decimal(str(
                (current_avg * (member.calls_handled - 1) + quality_score) / member.calls_handled
            ))
        
        if satisfaction is not None:
            current_avg = float(member.avg_satisfaction) if member.avg_satisfaction else 0
            member.avg_satisfaction = Decimal(str(
                (current_avg * (member.calls_handled - 1) + satisfaction) / member.calls_handled
            ))
        
        db.commit()
        
        return {
            "member_id": member_id,
            "calls_handled": member.calls_handled,
            "avg_quality_score": float(member.avg_quality_score) if member.avg_quality_score else None
        }
    
    def get_availability_overview(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Get real-time availability overview"""
        from app.models.models import TeamMember
        
        members = db.query(TeamMember).filter(
            TeamMember.business_id == business_id,
            TeamMember.status == "active"
        ).all()
        
        available = []
        unavailable = []
        
        for member in members:
            member_data = {
                "id": member.id,
                "name": member.name,
                "department": member.department,
                "role": member.role
            }
            
            if self._is_member_available(member):
                available.append(member_data)
            else:
                unavailable.append(member_data)
        
        return {
            "total_active": len(members),
            "currently_available": len(available),
            "available": available,
            "unavailable": unavailable
        }
    
    def get_performance_leaderboard(
        self,
        db: Session,
        business_id: int,
        metric: str = "quality_score",
        limit: int = 10
    ) -> List[Dict]:
        """Get performance leaderboard"""
        from app.models.models import TeamMember
        
        members = db.query(TeamMember).filter(
            TeamMember.business_id == business_id,
            TeamMember.status == "active"
        ).all()
        
        leaderboard = [
            {
                "id": m.id,
                "name": m.name,
                "quality_score": float(m.avg_quality_score) if m.avg_quality_score else 0,
                "calls_handled": m.calls_handled or 0,
                "satisfaction": float(m.avg_satisfaction) if m.avg_satisfaction else 0
            }
            for m in members
        ]
        
        # Sort by metric
        if metric == "quality_score":
            leaderboard.sort(key=lambda x: x["quality_score"], reverse=True)
        elif metric == "calls_handled":
            leaderboard.sort(key=lambda x: x["calls_handled"], reverse=True)
        elif metric == "satisfaction":
            leaderboard.sort(key=lambda x: x["satisfaction"], reverse=True)
        
        return leaderboard[:limit]
    
    def get_team_insights(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Generate insights about team performance"""
        from app.models.models import TeamMember, CallSession
        
        members = db.query(TeamMember).filter(
            TeamMember.business_id == business_id
        ).all()
        
        insights = []
        
        # Identify top performers
        top_performers = [m for m in members if m.avg_quality_score and float(m.avg_quality_score) > 80]
        if top_performers:
            insights.append({
                "type": "success",
                "message": f"{len(top_performers)} team member(s) have quality scores above 80%",
                "action": "Consider recognizing top performers"
            })
        
        # Identify members needing improvement
        needs_improvement = [m for m in members if m.avg_quality_score and float(m.avg_quality_score) < 60]
        if needs_improvement:
            insights.append({
                "type": "warning",
                "message": f"{len(needs_improvement)} team member(s) have quality scores below 60%",
                "action": "Consider additional training or coaching"
            })
        
        # Check staffing levels
        available = len([m for m in members if m.status == "active" and self._is_member_available(m)])
        if available == 0:
            insights.append({
                "type": "alert",
                "message": "No team members currently available",
                "action": "Check scheduling or contact backup staff"
            })
        
        return {
            "insights": insights,
            "team_size": len(members),
            "active_members": len([m for m in members if m.status == "active"])
        }


# Singleton instance
team_management_service = TeamManagementService()
