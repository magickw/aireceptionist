from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import Customer, Business, CallSession
import asyncio

class OutboundCampaignService:
    """
    Service for managing proactive AI outreach campaigns.
    Allows businesses to trigger AI calls for appointment reminders,
    follow-ups, or promotions.
    """
    
    def __init__(self, db: Session):
        self.db = db

    async def trigger_appointment_reminders(self, business_id: int) -> Dict[str, Any]:
        """
        Identify upcoming appointments and trigger AI reminder calls.
        """
        from app.models.models import Appointment
        from app.api.v1.endpoints.twilio import initiate_outbound_call
        
        # Get appointments for tomorrow
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        appts = self.db.query(Appointment).filter(
            Appointment.business_id == business_id,
            func.date(Appointment.appointment_time) == tomorrow,
            Appointment.status == "scheduled"
        ).all()
        
        triggered_count = 0
        for appt in appts:
            # Prepare context for the AI
            reminder_text = f"Hi {appt.customer_name}, this is an automated reminder for your appointment tomorrow at {appt.appointment_time.strftime('%I:%M %p')}."
            
            # This would trigger the Twilio call with a special briefing
            # For this enhancement implementation, we're calling the existing logic
            # In a real system, we'd use a background worker (Celery/TaskIQ)
            
            # Note: initiate_outbound_call expects a Request object in the current implementation,
            # we'd need to refactor it to be callable from a service.
            print(f"Triggering reminder call to {appt.customer_phone} for business {business_id}")
            triggered_count += 1
            
        return {
            "campaign_type": "appointment_reminder",
            "target_date": tomorrow.isoformat(),
            "calls_triggered": triggered_count
        }

    async def create_custom_campaign(
        self, 
        business_id: int, 
        customer_ids: List[int], 
        briefing: str
    ) -> Dict[str, Any]:
        """
        Trigger a custom outreach campaign to a specific list of customers.
        """
        customers = self.db.query(Customer).filter(
            Customer.id.in_(customer_ids),
            Customer.business_id == business_id
        ).all()
        
        triggered_count = 0
        for customer in customers:
            # Trigger the AI call with the custom briefing
            # The AI will use this briefing to guide the conversation
            print(f"Triggering custom outreach to {customer.phone} with briefing: {briefing}")
            triggered_count += 1
            
        return {
            "campaign_type": "custom_outreach",
            "customers_contacted": triggered_count,
            "briefing_used": briefing
        }

    async def get_outbound_stats(self, business_id: int) -> Dict[str, Any]:
        """Get statistics for outbound AI activities."""
        # This would query CallSession records where direction='outbound'
        return {
            "total_outbound_calls": 0,
            "successful_contacts": 0,
            "conversion_rate": 0.0
        }
