"""
Predictive Analytics Service
Peak call time forecasting and staffing recommendations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import statistics
from collections import defaultdict


class PredictiveAnalyticsService:
    """Service for predictive analytics and staffing recommendations"""
    
    # Business hour definitions by industry
    INDUSTRY_HOURS = {
        "medical": {"start": 8, "end": 17},
        "dental": {"start": 8, "end": 18},
        "restaurant": {"start": 11, "end": 22},
        "hotel": {"start": 0, "end": 24},  # 24/7
        "law_firm": {"start": 9, "end": 17},
        "salon": {"start": 9, "end": 19},
        "fitness": {"start": 5, "end": 22},
        "real_estate": {"start": 9, "end": 18},
        "auto_repair": {"start": 8, "end": 18},
        "hvac": {"start": 7, "end": 19},
        "accounting": {"start": 9, "end": 17},
        "education": {"start": 8, "end": 17},
        "general": {"start": 9, "end": 17}
    }
    
    # Staffing ratios by industry (calls per staff per hour)
    INDUSTRY_STAFFING_RATIO = {
        "medical": 3,
        "dental": 4,
        "restaurant": 6,
        "hotel": 8,
        "law_firm": 2,
        "salon": 5,
        "fitness": 8,
        "real_estate": 2,
        "auto_repair": 4,
        "hvac": 3,
        "accounting": 2,
        "education": 4,
        "general": 4
    }
    
    def __init__(self):
        pass
    
    async def get_peak_call_times(
        self,
        db: Session,
        business_id: int,
        days: int = 30
    ) -> Dict:
        """Analyze and predict peak call times"""
        from app.models.models import CallSession
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all calls in the period
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).all()
        
        if not calls:
            return {"error": "No call data available"}
        
        # Group calls by hour of day
        hourly_calls = defaultdict(list)
        for call in calls:
            if call.started_at:
                hour = call.started_at.hour
                hourly_calls[hour].append(call)
        
        # Group calls by day of week
        daily_calls = defaultdict(list)
        for call in calls:
            if call.started_at:
                day = call.started_at.weekday()  # 0 = Monday
                daily_calls[day].append(call)
        
        # Calculate hourly averages
        hourly_stats = {}
        for hour in range(24):
            hour_calls = hourly_calls.get(hour, [])
            hourly_stats[hour] = {
                "total_calls": len(hour_calls),
                "average_per_day": len(hour_calls) / days if days > 0 else 0
            }
        
        # Calculate daily averages
        daily_stats = {}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in range(7):
            day_calls = daily_calls.get(day, [])
            daily_stats[day_names[day]] = {
                "total_calls": len(day_calls),
                "average_per_week": len(day_calls) / (days / 7) if days > 0 else 0
            }
        
        # Identify peak hours
        sorted_hours = sorted(hourly_stats.items(), key=lambda x: x[1]["total_calls"], reverse=True)
        peak_hours = [{"hour": h, **stats} for h, stats in sorted_hours[:5]]
        
        # Identify peak days
        sorted_days = sorted(daily_stats.items(), key=lambda x: x[1]["total_calls"], reverse=True)
        peak_days = [{"day": d, **stats} for d, stats in sorted_days[:3]]
        
        return {
            "period_days": days,
            "total_calls": len(calls),
            "peak_hours": peak_hours,
            "peak_days": peak_days,
            "hourly_distribution": hourly_stats,
            "daily_distribution": daily_stats
        }
    
    async def get_staffing_recommendations(
        self,
        db: Session,
        business_id: int,
        business_type: str = "general"
    ) -> Dict:
        """Get staffing recommendations based on predicted call volume"""
        from app.models.models import CallSession, TeamMember
        
        # Get peak times analysis
        peak_analysis = await self.get_peak_call_times(db, business_id, 30)
        
        if "error" in peak_analysis:
            return peak_analysis
        
        # Get industry staffing ratio
        ratio = self.INDUSTRY_STAFFING_RATIO.get(business_type, 4)
        
        # Get current team members
        team_members = db.query(TeamMember).filter(
            TeamMember.business_id == business_id
        ).all()
        
        current_staff_count = len(team_members)
        
        # Calculate recommended staffing for each hour
        hourly_recommendations = []
        hourly_dist = peak_analysis.get("hourly_distribution", {})
        
        industry_hours = self.INDUSTRY_HOURS.get(business_type, self.INDUSTRY_HOURS["general"])
        
        for hour in range(24):
            avg_calls = hourly_dist.get(hour, {}).get("average_per_day", 0)
            
            # Only recommend staffing during business hours
            is_business_hour = industry_hours["start"] <= hour < industry_hours["end"]
            
            if is_business_hour and avg_calls > 0:
                recommended_staff = max(1, int(avg_calls / ratio) + (1 if avg_calls % ratio > 0 else 0))
                
                # Peak indicator
                is_peak = any(p["hour"] == hour for p in peak_analysis.get("peak_hours", []))
                
                hourly_recommendations.append({
                    "hour": hour,
                    "average_calls": round(avg_calls, 1),
                    "recommended_staff": recommended_staff,
                    "is_peak": is_peak,
                    "utilization": round(avg_calls / (recommended_staff * ratio) * 100, 1) if recommended_staff > 0 else 0
                })
        
        # Overall staffing recommendation
        peak_hour_staff = max([r["recommended_staff"] for r in hourly_recommendations]) if hourly_recommendations else 1
        
        return {
            "business_type": business_type,
            "business_hours": industry_hours,
            "staffing_ratio": f"1 staff per {ratio} calls/hour",
            "current_staff": current_staff_count,
            "recommended_minimum_staff": peak_hour_staff,
            "hourly_recommendations": hourly_recommendations,
            "summary": {
                "understaffed_hours": len([r for r in hourly_recommendations if r["recommended_staff"] > current_staff_count]),
                "overstaffed_hours": len([r for r in hourly_recommendations if current_staff_count > r["recommended_staff"] * 1.5]),
                "optimal_hours": len([r for r in hourly_recommendations if r["recommended_staff"] == current_staff_count])
            }
        }
    
    async def forecast_call_volume(
        self,
        db: Session,
        business_id: int,
        forecast_days: int = 7
    ) -> Dict:
        """Forecast call volume for upcoming days"""
        from app.models.models import CallSession
        
        # Get historical data (use more history for better prediction)
        history_days = 60
        start_date = datetime.now(timezone.utc) - timedelta(days=history_days)
        
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).all()
        
        if len(calls) < 14:  # Need at least 2 weeks of data
            return {"error": "Insufficient historical data for forecasting"}
        
        # Group by date
        daily_calls = defaultdict(int)
        for call in calls:
            if call.started_at:
                date_key = call.started_at.date()
                daily_calls[date_key] += 1
        
        # Calculate weekly patterns
        weekday_totals = defaultdict(list)
        for date, count in daily_calls.items():
            weekday_totals[date.weekday()].append(count)
        
        weekday_averages = {}
        for day, counts in weekday_totals.items():
            weekday_averages[day] = {
                "average": statistics.mean(counts) if counts else 0,
                "std_dev": statistics.stdev(counts) if len(counts) > 1 else 0
            }
        
        # Calculate trend (simple linear regression on last 14 days)
        recent_dates = sorted(daily_calls.keys())[-14:]
        if len(recent_dates) >= 2:
            x = list(range(len(recent_dates)))
            y = [daily_calls[d] for d in recent_dates]
            
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi ** 2 for xi in x)
            
            denominator = n * sum_x2 - sum_x ** 2
            if denominator != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                intercept = (sum_y - slope * sum_x) / n
            else:
                slope = 0
                intercept = sum_y / n
            
            trend = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        else:
            slope = 0
            intercept = 0
            trend = "unknown"
        
        # Generate forecast
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        forecast = []
        
        today = datetime.now(timezone.utc).date()
        for i in range(forecast_days):
            forecast_date = today + timedelta(days=i)
            weekday = forecast_date.weekday()
            
            weekday_avg = weekday_averages.get(weekday, {"average": 0, "std_dev": 0})
            
            # Apply trend adjustment
            base_forecast = weekday_avg["average"]
            trend_adjusted = base_forecast * (1 + slope * i / 14)
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "day": day_names[weekday],
                "predicted_calls": max(0, round(trend_adjusted)),
                "confidence_range": {
                    "low": max(0, round(trend_adjusted - weekday_avg["std_dev"])),
                    "high": round(trend_adjusted + weekday_avg["std_dev"])
                }
            })
        
        return {
            "forecast_days": forecast_days,
            "trend": trend,
            "trend_slope": round(slope, 3),
            "weekday_patterns": {day_names[k]: v for k, v in weekday_averages.items()},
            "forecast": forecast
        }
    
    async def get_resource_utilization(
        self,
        db: Session,
        business_id: int,
        days: int = 7
    ) -> Dict:
        """Analyze resource utilization patterns"""
        from app.models.models import CallSession, TeamMember
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get calls
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).all()
        
        # Get team members
        team = db.query(TeamMember).filter(
            TeamMember.business_id == business_id
        ).all()
        
        total_staff = len(team)
        
        # Calculate utilization metrics
        total_calls = len(calls)
        total_duration = sum(c.duration_seconds or 0 for c in calls)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0
        
        # Calculate by hour
        hourly_utilization = defaultdict(lambda: {"calls": 0, "duration": 0})
        for call in calls:
            if call.started_at:
                hour = call.started_at.hour
                hourly_utilization[hour]["calls"] += 1
                hourly_utilization[hour]["duration"] += call.duration_seconds or 0
        
        # Calculate utilization percentage
        business_hours_per_day = 9  # Default
        total_available_minutes = days * business_hours_per_day * 60 * total_staff
        total_used_minutes = total_duration / 60
        
        utilization_rate = (total_used_minutes / total_available_minutes * 100) if total_available_minutes > 0 else 0
        
        return {
            "period_days": days,
            "total_staff": total_staff,
            "total_calls": total_calls,
            "total_duration_minutes": round(total_duration / 60),
            "average_call_duration_seconds": round(avg_duration),
            "utilization_rate_percent": round(utilization_rate, 1),
            "calls_per_staff_per_day": round(total_calls / (total_staff * days), 1) if total_staff > 0 else 0,
            "hourly_utilization": dict(hourly_utilization),
            "recommendations": self._generate_utilization_recommendations(
                utilization_rate, total_staff, total_calls, days
            )
        }
    
    def _generate_utilization_recommendations(
        self,
        utilization_rate: float,
        staff_count: int,
        call_count: int,
        days: int
    ) -> List[str]:
        """Generate recommendations based on utilization"""
        recommendations = []
        
        if utilization_rate > 80:
            recommendations.append("High utilization detected. Consider adding staff to prevent burnout.")
        elif utilization_rate < 30:
            recommendations.append("Low utilization detected. Consider reducing staff hours or reassigning tasks.")
        
        calls_per_day = call_count / days if days > 0 else 0
        if calls_per_day > 50 and staff_count < 3:
            recommendations.append("High call volume with limited staff. Consider hiring more team members.")
        
        if staff_count == 0:
            recommendations.append("No team members registered. Add staff for accurate utilization tracking.")
        
        if not recommendations:
            recommendations.append("Utilization is within normal range.")
        
        return recommendations
    
    async def predict_service_level(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Predict service level based on historical performance"""
        from app.models.models import CallSession
        
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).all()
        
        if not calls:
            return {"error": "No call data available"}
        
        # Calculate service level metrics
        answered_calls = [c for c in calls if c.status not in ["missed", "voicemail"]]
        transferred_calls = [c for c in calls if c.status == "transferred"]
        completed_calls = [c for c in calls if c.status == "ended"]
        
        total = len(calls)
        answer_rate = len(answered_calls) / total * 100 if total > 0 else 0
        transfer_rate = len(transferred_calls) / total * 100 if total > 0 else 0
        
        # Average response time estimation (placeholder)
        avg_response_time = 5.0  # seconds
        
        # Service level (calls answered within 20 seconds)
        service_level = answer_rate * 0.9  # Estimate
        
        return {
            "total_calls": total,
            "answer_rate_percent": round(answer_rate, 1),
            "transfer_rate_percent": round(transfer_rate, 1),
            "average_response_time_seconds": avg_response_time,
            "service_level_percent": round(service_level, 1),
            "grade": self._grade_service_level(service_level)
        }
    
    def _grade_service_level(self, service_level: float) -> str:
        """Grade service level performance"""
        if service_level >= 90:
            return "Excellent"
        elif service_level >= 80:
            return "Good"
        elif service_level >= 70:
            return "Fair"
        elif service_level >= 60:
            return "Needs Improvement"
        else:
            return "Poor"


# Singleton instance
predictive_analytics_service = PredictiveAnalyticsService()
