"""
Forecasting Service - Call Volume Prediction
Uses historical data to predict future call volumes
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
import math


class ForecastingService:
    """Service for call volume forecasting using simple moving average and trend analysis"""
    
    def __init__(self):
        self.seasonal_patterns = {
            0: 0.9,   # Sunday
            1: 1.1,   # Monday
            2: 1.0,   # Tuesday
            3: 1.05,  # Wednesday
            4: 1.0,   # Thursday
            5: 0.95,  # Friday
            6: 0.85   # Saturday
        }
    
    def get_call_volume_history(
        self, 
        db: Session, 
        business_id: int, 
        days: int = 30
    ) -> List[Dict]:
        """Get historical call volume data"""
        from app.models.models import CallSession
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get call counts grouped by date
        results = db.query(
            func.date(CallSession.start_time).label('date'),
            func.count(CallSession.id).label('count')
        ).filter(
            CallSession.business_id == business_id,
            CallSession.start_time >= start_date
        ).group_by(
            func.date(CallSession.start_time)
        ).order_by(
            func.date(CallSession.start_time)
        ).all()
        
        return [{"date": str(r.date), "count": r.count} for r in results]
    
    def calculate_daily_average(self, history: List[Dict]) -> float:
        """Calculate average daily call volume"""
        if not history:
            return 0
        total = sum(h["count"] for h in history)
        return total / len(history)
    
    def calculate_trend(self, history: List[Dict]) -> float:
        """Calculate trend coefficient (-1 to 1)"""
        if len(history) < 7:
            return 0
        
        # Compare recent week to previous week
        recent = sum(h["count"] for h in history[-7:])
        previous = sum(h["count"] for h in history[-14:-7]) if len(history) >= 14 else recent
        
        if previous == 0:
            return 0
        
        return (recent - previous) / previous
    
    def predict_daily_volume(
        self, 
        db: Session, 
        business_id: int, 
        days_ahead: int = 7
    ) -> List[Dict]:
        """Predict call volume for upcoming days"""
        history = self.get_call_volume_history(db, business_id, days=30)
        
        if not history:
            return []
        
        daily_avg = self.calculate_daily_average(history)
        trend = self.calculate_trend(history)
        
        predictions = []
        base_date = datetime.now(timezone.utc).date()
        
        for i in range(1, days_ahead + 1):
            pred_date = base_date + timedelta(days=i)
            day_of_week = pred_date.weekday()
            
            # Apply trend and seasonal adjustment
            trend_factor = 1 + (trend * i / 7)  # Gradual trend application
            seasonal_factor = self.seasonal_patterns.get(day_of_week, 1.0)
            
            predicted_volume = int(daily_avg * trend_factor * seasonal_factor)
            
            predictions.append({
                "date": str(pred_date),
                "day_of_week": pred_date.strftime("%A"),
                "predicted_calls": max(0, predicted_volume),
                "confidence": self._calculate_confidence(i, len(history))
            })
        
        return predictions
    
    def _calculate_confidence(self, days_ahead: int, history_length: int) -> str:
        """Calculate prediction confidence level"""
        if history_length < 14:
            return "low"
        
        if days_ahead <= 3:
            return "high" if history_length >= 30 else "medium"
        elif days_ahead <= 7:
            return "medium" if history_length >= 21 else "low"
        else:
            return "low"
    
    def get_peak_hours(self, db: Session, business_id: int) -> List[Dict]:
        """Analyze peak calling hours"""
        from app.models.models import CallSession
        
        results = db.query(
            func.extract('hour', CallSession.start_time).label('hour'),
            func.count(CallSession.id).label('count')
        ).filter(
            CallSession.business_id == business_id,
            CallSession.start_time >= datetime.now(timezone.utc) - timedelta(days=30)
        ).group_by(
            func.extract('hour', CallSession.start_time)
        ).order_by(
            func.count(CallSession.id).desc()
        ).limit(5).all()
        
        return [{"hour": int(r.hour), "count": r.count} for r in results]
    
    def get_weekly_forecast_summary(
        self, 
        db: Session, 
        business_id: int
    ) -> Dict:
        """Get weekly forecast summary with insights"""
        predictions = self.predict_daily_volume(db, business_id, days_ahead=7)
        history = self.get_call_volume_history(db, business_id, days=7)
        
        weekly_total = sum(p["predicted_calls"] for p in predictions)
        historical_weekly = sum(h["count"] for h in history)
        
        trend = "increasing" if weekly_total > historical_weekly else "decreasing" if weekly_total < historical_weekly else "stable"
        
        return {
            "predictions": predictions,
            "weekly_total_predicted": weekly_total,
            "historical_weekly_average": historical_weekly,
            "trend": trend,
            "change_percentage": round((weekly_total - historical_weekly) / max(historical_weekly, 1) * 100, 1),
            "peak_hours": self.get_peak_hours(db, business_id)
        }


forecasting_service = ForecastingService()
