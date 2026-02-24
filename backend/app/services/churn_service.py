"""
Customer Churn Prediction Service
Predicts customer churn risk based on call patterns
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func


class ChurnService:
    """Service for predicting customer churn risk"""
    
    def __init__(self):
        self.risk_weights = {
            "no_calls_days": 30,      # Days without calling
            "negative_sentiment": 25,  # Negative call sentiment
            "missed_calls": 20,        # Multiple missed calls
            "short_calls": 15,         # Very short interactions
            "no_appointments": 20,     # No appointments scheduled
        }
    
    def calculate_churn_risk(
        self, 
        db: Session, 
        customer_phone: str, 
        business_id: int
    ) -> Dict:
        """Calculate churn risk for a customer"""
        from app.models.models import CallSession, Appointment
        
        risk_score = 0
        factors = []
        
        # Check last call date
        last_call = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone == customer_phone
        ).order_by(CallSession.start_time.desc()).first()
        
        if last_call:
            days_since_last_call = (datetime.now(timezone.utc) - last_call.start_time).days
            
            if days_since_last_call > 60:
                risk_score += self.risk_weights["no_calls_days"]
                factors.append({
                    "factor": "no_calls_60_days",
                    "weight": self.risk_weights["no_calls_days"],
                    "value": days_since_last_call
                })
            elif days_since_last_call > 30:
                risk_score += self.risk_weights["no_calls_days"] // 2
                factors.append({
                    "factor": "no_calls_30_days",
                    "weight": self.risk_weights["no_calls_days"] // 2,
                    "value": days_since_last_call
                })
            
            # Check sentiment
            if last_call.sentiment == "negative":
                risk_score += self.risk_weights["negative_sentiment"]
                factors.append({
                    "factor": "negative_sentiment",
                    "weight": self.risk_weights["negative_sentiment"]
                })
            
            # Check call duration
            if last_call.end_time and last_call.start_time:
                duration = (last_call.end_time - last_call.start_time).seconds
                if duration < 30:  # Less than 30 seconds
                    risk_score += self.risk_weights["short_calls"]
                    factors.append({
                        "factor": "short_call",
                        "weight": self.risk_weights["short_calls"],
                        "value": duration
                    })
        else:
            risk_score += self.risk_weights["no_calls_days"]
            factors.append({
                "factor": "no_calls_ever",
                "weight": self.risk_weights["no_calls_days"]
            })
        
        # Check missed calls
        missed_calls = db.query(func.count(CallSession.id)).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone == customer_phone,
            CallSession.status == "missed"
        ).scalar() or 0
        
        if missed_calls >= 3:
            risk_score += self.risk_weights["missed_calls"]
            factors.append({
                "factor": "multiple_missed_calls",
                "weight": self.risk_weights["missed_calls"],
                "value": missed_calls
            })
        
        # Check appointments
        has_appointment = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.customer_phone == customer_phone,
            Appointment.start_time > datetime.now(timezone.utc)
        ).first()
        
        if not has_appointment:
            risk_score += self.risk_weights["no_appointments"]
            factors.append({
                "factor": "no_upcoming_appointments",
                "weight": self.risk_weights["no_appointments"]
            })
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "customer_phone": customer_phone,
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "factors": factors,
            "last_call": last_call.start_time.isoformat() if last_call else None
        }
    
    def get_at_risk_customers(
        self, 
        db: Session, 
        business_id: int,
        min_risk_score: int = 40
    ) -> List[Dict]:
        """Get all customers with churn risk"""
        from app.models.models import CallSession
        
        # Get unique customer phones
        customers = db.query(
            CallSession.customer_phone,
            func.max(CallSession.start_time).label('last_call')
        ).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone.isnot(None)
        ).group_by(
            CallSession.customer_phone
        ).all()
        
        at_risk = []
        for customer in customers:
            risk = self.calculate_churn_risk(db, customer.customer_phone, business_id)
            if risk["risk_score"] >= min_risk_score:
                at_risk.append(risk)
        
        # Sort by risk score
        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return at_risk
    
    def get_churn_stats(
        self, 
        db: Session, 
        business_id: int
    ) -> Dict:
        """Get overall churn statistics"""
        at_risk = self.get_at_risk_customers(db, business_id, min_risk_score=40)
        
        high_risk = sum(1 for c in at_risk if c["risk_level"] == "high")
        medium_risk = sum(1 for c in at_risk if c["risk_level"] == "medium")
        low_risk = sum(1 for c in at_risk if c["risk_level"] == "low")
        
        total = len(at_risk)
        
        return {
            "total_at_risk": total,
            "distribution": {
                "high": high_risk,
                "medium": medium_risk,
                "low": low_risk
            },
            "percentages": {
                "high": round(high_risk / max(total, 1) * 100, 1),
                "medium": round(medium_risk / max(total, 1) * 100, 1),
                "low": round(low_risk / max(total, 1) * 100, 1)
            }
        }


churn_service = ChurnService()
