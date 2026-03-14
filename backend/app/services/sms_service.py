"""
SMS Notification Service

Handles:
- Twilio SMS/MMS sending
- Template management
- Automated follow-ups based on events
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import SMSTemplate, Appointment, CallSession
from app.core.config import settings


def validate_e164_phone_number(phone: str) -> tuple[bool, str]:
    """
    Validate phone number is in E.164 format.
    Returns (is_valid, error_message).
    """
    if not phone:
        return False, "Phone number is required"
    
    # E.164 format: +[country code][number], max 15 digits
    e164_pattern = r'^\+[1-9]\d{1,14}$'
    if not re.match(e164_pattern, phone):
        return False, f"Phone number must be in E.164 format (e.g., +12345678900), got: {phone}"
    
    return True, ""


class SMSService:
    """Service for sending SMS notifications via Twilio"""
    
    def __init__(self):
        # Twilio configuration from centralized settings
        self.enabled = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER)
    
    async def send_sms(
        self,
        to_number: str,
        message: str,
        media_url: str = None
    ) -> Dict[str, Any]:
        """
        Send an SMS via Twilio.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS content
            media_url: Optional MMS media URL
            
        Returns:
            Dict with Twilio message SID and status
        """
        if not self.enabled:
            return {"success": False, "error": "Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables."}
        
        # Validate phone number format
        is_valid, error_msg = validate_e164_phone_number(to_number)
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            msg_params = {
                "body": message,
                "from_": settings.TWILIO_PHONE_NUMBER,
                "to": to_number
            }
            
            if media_url:
                msg_params["media_url"] = media_url
            
            twilio_message = client.messages.create(**msg_params)
            
            return {
                "success": True,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Twilio library not installed. Run: pip install twilio"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_appointment_reminder(
        self,
        appointment: Appointment,
        db: Session
    ) -> Dict[str, Any]:
        """Send appointment reminder SMS"""
        # Get template
        template = db.query(SMSTemplate).filter(
            SMSTemplate.business_id == appointment.business_id,
            SMSTemplate.event_type == "appointment.reminder",
            SMSTemplate.is_active == True
        ).first()
        
        if not template:
            # Default template
            message = f"Reminder: You have an appointment scheduled for {appointment.appointment_time}"
        else:
            message = self._render_template(
                template.content,
                appointment=appointment
            )
        
        return await self.send_sms(
            to_number=appointment.customer_phone,
            message=message
        )
    
    async def send_call_summary_sms(
        self,
        call_session: CallSession,
        db: Session
    ) -> Dict[str, Any]:
        """Send post-call summary SMS"""
        template = db.query(SMSTemplate).filter(
            SMSTemplate.business_id == call_session.business_id,
            SMSTemplate.event_type == "call.summary",
            SMSTemplate.is_active == True
        ).first()
        
        if not template:
            message = f"Thanks for calling! Your call summary: {call_session.summary or 'No summary available'}"
        else:
            message = self._render_template(
                template.content,
                call_session=call_session
            )
        
        return await self.send_sms(
            to_number=call_session.customer_phone,
            message=message
        )
    
    def _render_template(
        self,
        template: str,
        **kwargs
    ) -> str:
        """Render SMS template with variables"""
        import re
        
        # Simple template variable replacement
        # Variables format: {{variable_name}}
        def replace_var(match):
            key = match.group(1).strip()
            obj = kwargs.get(key.split('.')[0])
            
            if not obj:
                return match.group(0)
            
            # Handle nested attributes (e.g., appointment.customer_name)
            parts = key.split('.')
            value = obj
            for part in parts[1:]:
                value = getattr(value, part, None)
                if value is None:
                    return match.group(0)
            
            return str(value)
        
        return re.sub(r'\{\{(.*?)\}\}', replace_var, template)
    
    # Template management
    def list_templates(
        self,
        business_id: int,
        db: Session,
        active_only: bool = True
    ) -> List[SMSTemplate]:
        """List SMS templates for a business"""
        query = db.query(SMSTemplate).filter(
            SMSTemplate.business_id == business_id
        )
        
        if active_only:
            query = query.filter(SMSTemplate.is_active == True)
        
        return query.order_by(desc(SMSTemplate.created_at)).all()
    
    def get_template(
        self,
        template_id: int,
        business_id: int,
        db: Session
    ) -> Optional[SMSTemplate]:
        """Get a specific template"""
        return db.query(SMSTemplate).filter(
            SMSTemplate.id == template_id,
            SMSTemplate.business_id == business_id
        ).first()
    
    def create_template(
        self,
        business_id: int,
        name: str,
        event_type: str,
        content: str,
        db: Session,
        is_active: bool = True
    ) -> SMSTemplate:
        """Create a new SMS template"""
        # Validate event type
        valid_events = [
            "appointment.reminder",
            "appointment.confirmation",
            "appointment.cancellation",
            "call.summary",
            "custom"
        ]
        
        if event_type not in valid_events:
            raise ValueError(f"Invalid event type. Must be one of: {valid_events}")
        
        template = SMSTemplate(
            business_id=business_id,
            name=name,
            event_type=event_type,
            content=content,
            is_active=is_active
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    def update_template(
        self,
        template_id: int,
        business_id: int,
        db: Session,
        **updates
    ) -> Optional[SMSTemplate]:
        """Update a template"""
        template = self.get_template(template_id, business_id, db)
        if not template:
            return None
        
        for key, value in updates.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)
        
        db.commit()
        db.refresh(template)
        return template
    
    def delete_template(
        self,
        template_id: int,
        business_id: int,
        db: Session
    ) -> bool:
        """Delete a template"""
        template = self.get_template(template_id, business_id, db)
        if not template:
            return False
        
        db.delete(template)
        db.commit()
        return True
    
    def get_default_templates(self) -> List[Dict[str, str]]:
        """Get default SMS templates"""
        return [
            {
                "name": "Appointment Reminder",
                "event_type": "appointment.reminder",
                "content": "Hi {{appointment.customer_name}}! This is a reminder for your appointment on {{appointment.appointment_time}}. Reply YES to confirm or call us to reschedule."
            },
            {
                "name": "Appointment Confirmation",
                "event_type": "appointment.confirmation",
                "content": "Hi {{appointment.customer_name}}! Your appointment has been confirmed for {{appointment.appointment_time}}. We look forward to seeing you!"
            },
            {
                "name": "Call Summary",
                "event_type": "call.summary",
                "content": "Thanks for calling! Your call summary: {{call_session.summary}}"
            }
        ]


# Singleton instance
sms_service = SMSService()
