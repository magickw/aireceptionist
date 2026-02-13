from typing import Any, Dict, List
from fastapi import APIRouter, Depends
import random
from datetime import datetime, timedelta

from app.api import deps
from app.models.models import User

router = APIRouter()

@router.get("/business/{business_id}")
def get_analytics(
    business_id: int,
    timeframe: str = "30d",
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get comprehensive analytics for a business (Mock Data).
    """
    # Generate realistic mock data
    return {
      "totalCalls": random.randint(100, 600),
      "avgCallDuration": random.randint(120, 300),
      "appointmentsBooked": random.randint(20, 70),
      "successRate": random.randint(80, 100),
      "dailyTrends": generate_mock_daily_trends(timeframe),
      "intentAnalysis": [
        { "intent": 'appointment_booking', "count": 45, "avg_confidence": 0.92 },
        { "intent": 'general_inquiry', "count": 32, "avg_confidence": 0.87 },
        { "intent": 'support_request', "count": 28, "avg_confidence": 0.89 },
        { "intent": 'service_info', "count": 21, "avg_confidence": 0.85 },
        { "intent": 'pricing_inquiry', "count": 18, "avg_confidence": 0.91 }
      ],
      "peakHours": generate_mock_peak_hours(),
      "timeframe": timeframe
    }

@router.get("/business/{business_id}/revenue")
def get_revenue_analytics(
    business_id: int,
    timeframe: str = "30d",
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    avg_appointment_value = 150
    appointment_revenue = generate_mock_revenue_trends(timeframe)
    total_revenue = sum(day["revenue"] for day in appointment_revenue)

    return {
      "totalRevenue": total_revenue,
      "avgAppointmentValue": avg_appointment_value,
      "appointmentRevenue": appointment_revenue,
      "timeframe": timeframe
    }

@router.get("/business/{business_id}/realtime")
def get_realtime_analytics(
    business_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return {
      "activeCalls": random.randint(0, 5),
      "todayStats": {
        "calls_today": random.randint(5, 30),
        "avg_duration_today": random.randint(120, 180),
        "completed_calls": random.randint(5, 25)
      },
      "recentCalls": generate_mock_recent_calls()
    }

# Helper functions
def generate_mock_daily_trends(timeframe: str):
    days = 7 if timeframe == '7d' else 30 if timeframe == '30d' else 90
    trends = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "calls": random.randint(5, 25),
            "avg_duration": random.randint(120, 180),
            "avg_confidence": round(random.uniform(0.7, 1.0), 2)
        })
    return trends

def generate_mock_peak_hours():
    hours = []
    for hour in range(24):
        calls = 0
        if 8 <= hour <= 18:
            calls = random.randint(5, 20)
        elif 19 <= hour <= 21:
            calls = random.randint(2, 10)
        else:
            calls = random.randint(0, 3)
        hours.append({ "hour": hour, "calls": calls })
    return hours

def generate_mock_revenue_trends(timeframe: str):
    days = 7 if timeframe == '7d' else 30 if timeframe == '30d' else 90
    trends = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        appointments = random.randint(1, 6)
        trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "total_appointments": appointments,
            "revenue": appointments * 150
        })
    return trends

def generate_mock_recent_calls():
    calls = []
    phone_numbers = ['+1234567890', '+1987654321', '+1555123456', '+1444555666', '+1777888999']
    statuses = ['ended', 'active', 'ended', 'ended', 'ended']
    
    for i in range(5):
        start_time = datetime.now() - timedelta(minutes=(i * 30 + random.randint(0, 60)))
        calls.append({
            "id": f"call_{i + 1}",
            "customer_phone": phone_numbers[i],
            "status": statuses[i],
            "started_at": start_time.isoformat(),
            "duration_seconds": random.randint(60, 360),
            "ai_confidence": round(random.uniform(0.7, 1.0), 2)
        })
    return calls
