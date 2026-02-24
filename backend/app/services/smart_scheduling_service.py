"""
Smart Scheduling Service
Provides optimal appointment suggestions and no-show prediction
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class SmartSchedulingService:
    """Service for intelligent appointment scheduling with no-show prediction"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
    
    async def predict_no_show_probability(
        self, 
        db: Session,
        business_id: int,
        customer_phone: str,
        appointment_time: datetime,
        service_type: str = None
    ) -> Dict:
        """
        Predict the probability of a customer being a no-show.
        Uses historical data and AI analysis.
        """
        from app.models.models import Appointment, Customer, CallSession
        
        # Get customer history
        customer = db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.phone == customer_phone
        ).first()
        
        # Get historical appointment data
        historical_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.customer_phone == customer_phone
        ).all()
        
        # Calculate base probability from historical data
        base_probability = self._calculate_historical_no_show_rate(historical_appointments)
        
        # Adjust for time factors
        time_adjusted_prob = self._adjust_for_time_factors(
            appointment_time, 
            base_probability
        )
        
        # Adjust for customer factors
        customer_factors = {}
        if customer:
            customer_factors = {
                "total_appointments": customer.total_appointments or 0,
                "loyalty_tier": customer.loyalty_tier,
                "churn_risk": float(customer.churn_risk) if customer.churn_risk else 0,
                "is_vip": customer.is_vip
            }
            
            # VIP and loyal customers less likely to no-show
            if customer.is_vip or customer.loyalty_tier in ["gold", "platinum"]:
                time_adjusted_prob *= 0.6
            elif customer.loyalty_tier == "silver":
                time_adjusted_prob *= 0.8
        
        # Adjust for day of week and time
        time_adjusted_prob = self._adjust_for_slot_popularity(
            db, business_id, appointment_time, time_adjusted_prob
        )
        
        final_probability = min(1.0, max(0.0, time_adjusted_prob))
        
        # Generate risk level and recommendations
        if final_probability >= 0.6:
            risk_level = "high"
            recommendation = "Consider sending multiple reminders or requiring confirmation"
        elif final_probability >= 0.3:
            risk_level = "medium"
            recommendation = "Send a reminder 24 hours before"
        else:
            risk_level = "low"
            recommendation = "Standard confirmation is sufficient"
        
        return {
            "no_show_probability": round(final_probability, 2),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "factors": {
                "historical_no_show_rate": base_probability,
                "time_adjustment": time_adjusted_prob - base_probability,
                "customer_factors": customer_factors
            },
            "confidence": 0.7 if historical_appointments else 0.4
        }
    
    def _calculate_historical_no_show_rate(self, appointments: List) -> float:
        """Calculate historical no-show rate from past appointments"""
        if not appointments:
            return 0.25  # Default average no-show rate
        
        completed = [a for a in appointments if a.status in ["completed", "no_show", "cancelled"]]
        if not completed:
            return 0.25
        
        no_shows = sum(1 for a in completed if a.status == "no_show")
        return no_shows / len(completed)
    
    def _adjust_for_time_factors(self, appointment_time: datetime, base_prob: float) -> float:
        """Adjust probability based on time factors"""
        adjusted = base_prob
        
        # Monday morning appointments have higher no-show rates
        if appointment_time.weekday() == 0 and appointment_time.hour < 10:
            adjusted *= 1.2
        
        # Friday afternoon appointments also have higher no-show rates
        if appointment_time.weekday() == 4 and appointment_time.hour >= 14:
            adjusted *= 1.15
        
        # Early morning (before 9am) has higher no-show
        if appointment_time.hour < 9:
            adjusted *= 1.1
        
        # Mid-day appointments (10am-2pm) have lower no-show
        if 10 <= appointment_time.hour <= 14:
            adjusted *= 0.9
        
        return adjusted
    
    def _adjust_for_slot_popularity(
        self, 
        db: Session, 
        business_id: int, 
        appointment_time: datetime,
        current_prob: float
    ) -> float:
        """Adjust based on slot popularity and business patterns"""
        from app.models.models import Appointment
        
        # Count appointments in similar time slots
        similar_time_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.status == "no_show",
            func.extract('hour', Appointment.appointment_time) == appointment_time.hour,
            func.extract('dow', Appointment.appointment_time) == appointment_time.weekday() + 1
        ).count()
        
        # If this time slot has historically high no-shows, increase probability
        if similar_time_appointments > 3:
            current_prob *= 1.1
        
        return current_prob
    
    async def suggest_optimal_times(
        self,
        db: Session,
        business_id: int,
        customer_phone: str,
        preferred_date: datetime,
        service_duration_minutes: int = 60,
        max_suggestions: int = 5
    ) -> Dict:
        """
        Suggest optimal appointment times based on:
        - Low no-show probability
        - Business operating hours
        - Existing appointments
        - Customer preferences
        """
        from app.models.models import Business, Appointment, Customer
        
        # Get business operating hours
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        operating_hours = business.operating_hours or {}
        day_of_week = preferred_date.strftime('%A').lower()
        
        # Get business hours for the day
        day_hours = operating_hours.get(day_of_week, {})
        if not day_hours or day_hours.get('closed', False):
            return {"error": f"Business is closed on {day_of_week}"}
        
        open_time = datetime.strptime(day_hours.get('open', '09:00'), '%H:%M').time()
        close_time = datetime.strptime(day_hours.get('close', '17:00'), '%H:%M').time()
        
        # Get existing appointments for the day
        day_start = preferred_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        existing_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.appointment_time >= day_start,
            Appointment.appointment_time < day_end,
            Appointment.status.in_(["scheduled", "confirmed"])
        ).order_by(Appointment.appointment_time).all()
        
        # Find available slots
        available_slots = self._find_available_slots(
            preferred_date, open_time, close_time,
            existing_appointments, service_duration_minutes
        )
        
        # Score each slot
        scored_slots = []
        for slot in available_slots:
            score = await self._score_time_slot(db, business_id, customer_phone, slot)
            scored_slots.append({
                "time": slot.isoformat(),
                "score": score["score"],
                "no_show_probability": score["no_show_probability"],
                "reasons": score["reasons"]
            })
        
        # Sort by score (lower is better) and return top suggestions
        scored_slots.sort(key=lambda x: x["score"])
        top_suggestions = scored_slots[:max_suggestions]
        
        return {
            "date": preferred_date.strftime('%Y-%m-%d'),
            "suggested_times": top_suggestions,
            "total_available_slots": len(available_slots),
            "operating_hours": {
                "open": day_hours.get('open'),
                "close": day_hours.get('close')
            }
        }
    
    def _find_available_slots(
        self,
        date: datetime,
        open_time,
        close_time,
        existing_appointments: List,
        duration_minutes: int
    ) -> List[datetime]:
        """Find available time slots for appointments"""
        slots = []
        slot_duration = timedelta(minutes=duration_minutes)
        buffer = timedelta(minutes=15)  # Buffer between appointments
        
        current_time = datetime.combine(date.date(), open_time)
        end_time = datetime.combine(date.date(), close_time)
        
        # Create list of blocked times
        blocked_times = []
        for appt in existing_appointments:
            appt_start = appt.appointment_time
            appt_end = appt_start + slot_duration
            blocked_times.append((appt_start, appt_end))
        
        # Find gaps
        while current_time + slot_duration <= end_time:
            slot_end = current_time + slot_duration
            
            # Check if slot overlaps with any blocked time
            is_available = True
            for block_start, block_end in blocked_times:
                if current_time < block_end and slot_end > block_start:
                    is_available = False
                    current_time = block_end + buffer
                    break
            
            if is_available:
                slots.append(current_time)
                current_time += slot_duration + buffer
            else:
                continue
        
        return slots
    
    async def _score_time_slot(
        self,
        db: Session,
        business_id: int,
        customer_phone: str,
        slot_time: datetime
    ) -> Dict:
        """Score a time slot based on multiple factors"""
        score = 0
        reasons = []
        
        # Get no-show probability
        no_show_prob = await self.predict_no_show_probability(
            db, business_id, customer_phone, slot_time
        )
        
        # Score based on no-show probability (lower is better)
        score += no_show_prob["no_show_probability"] * 50
        if no_show_prob["risk_level"] == "high":
            reasons.append("Higher no-show risk for this time")
        elif no_show_prob["risk_level"] == "low":
            reasons.append("Low no-show risk")
        
        # Score based on time preference (mid-day is preferred)
        hour = slot_time.hour
        if 10 <= hour <= 14:
            score -= 10
            reasons.append("Popular time slot")
        elif hour < 9:
            score += 5
            reasons.append("Early morning slot")
        
        # Score based on day of week
        if slot_time.weekday() in [0, 4]:  # Monday or Friday
            score += 5
        elif slot_time.weekday() in [1, 2, 3]:  # Tue-Thu
            score -= 5
            reasons.append("Mid-week appointment")
        
        return {
            "score": max(0, min(100, score)),
            "no_show_probability": no_show_prob["no_show_probability"],
            "reasons": reasons
        }
    
    async def get_scheduling_analytics(
        self,
        db: Session,
        business_id: int,
        days: int = 30
    ) -> Dict:
        """Get scheduling analytics and insights"""
        from app.models.models import Appointment
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.appointment_time >= start_date
        ).all()
        
        total = len(appointments)
        if total == 0:
            return {"total_appointments": 0}
        
        # Calculate metrics
        completed = sum(1 for a in appointments if a.status == "completed")
        no_shows = sum(1 for a in appointments if a.status == "no_show")
        cancelled = sum(1 for a in appointments if a.status == "cancelled")
        
        # Calculate by time of day
        morning = sum(1 for a in appointments if a.appointment_time.hour < 12)
        afternoon = sum(1 for a in appointments if a.appointment_time.hour >= 12)
        
        # Calculate by day of week
        by_day = {}
        for a in appointments:
            day_name = a.appointment_time.strftime('%A')
            by_day[day_name] = by_day.get(day_name, 0) + 1
        
        # Calculate no-show by time
        no_show_by_hour = {}
        for a in appointments:
            if a.status == "no_show":
                hour = a.appointment_time.hour
                no_show_by_hour[hour] = no_show_by_hour.get(hour, 0) + 1
        
        # Find peak hours
        peak_hours = sorted(no_show_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "period_days": days,
            "total_appointments": total,
            "completion_rate": round(completed / total * 100, 1),
            "no_show_rate": round(no_shows / total * 100, 1),
            "cancellation_rate": round(cancelled / total * 100, 1),
            "distribution": {
                "morning": morning,
                "afternoon": afternoon
            },
            "by_day": by_day,
            "peak_no_show_hours": [{"hour": h, "count": c} for h, c in peak_hours],
            "recommendations": self._generate_scheduling_recommendations(
                no_shows / total if total > 0 else 0
            )
        }
    
    def _generate_scheduling_recommendations(self, no_show_rate: float) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        if no_show_rate > 0.25:
            recommendations.append("High no-show rate detected. Consider implementing a deposit policy.")
            recommendations.append("Send automated reminders 24 hours and 1 hour before appointments.")
        elif no_show_rate > 0.15:
            recommendations.append("Moderate no-show rate. Consider sending reminders 24 hours before.")
        
        recommendations.append("Consider overbooking by 10-15% for high no-show time slots.")
        recommendations.append("Track customer no-show patterns and prioritize follow-ups with frequent no-shows.")
        
        return recommendations
    
    async def send_appointment_reminder(
        self,
        db: Session,
        appointment_id: int
    ) -> Dict:
        """Send appointment reminder and track response"""
        from app.models.models import Appointment
        from app.services.sms_service import sms_service
        
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return {"error": "Appointment not found"}
        
        # Check if reminder already sent
        if appointment.reminder_sent:
            return {"status": "already_sent"}
        
        # Format message
        appt_time = appointment.appointment_time.strftime('%B %d at %I:%M %p')
        message = f"Reminder: You have an appointment on {appt_time}. Reply 'C' to confirm or 'R' to reschedule."
        
        # Send SMS
        try:
            result = await sms_service.send_sms(
                to=appointment.customer_phone,
                message=message
            )
            
            # Mark reminder as sent
            appointment.reminder_sent = True
            db.commit()
            
            return {
                "status": "sent",
                "appointment_id": appointment_id,
                "message_sid": result.get("sid")
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
smart_scheduling_service = SmartSchedulingService()
