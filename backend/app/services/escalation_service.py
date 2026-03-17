"""
Escalation Notification Service

Handles multi-channel notifications when human intervention is required:
- SMS to emergency contact
- Push notification to business owner
- Webhook triggers for external integrations
- Fallback chain for unresponsive contacts
- State machine tracking (triggered -> notified -> acknowledged -> resolved)
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from enum import Enum
import logging

from app.models.models import Business, User, Escalation
from app.services.sms_service import sms_service
from app.services.mobile_app_service import mobile_app_service, NotificationType
from app.services.webhook_service import webhook_service

logger = logging.getLogger(__name__)


class EscalationLevel(str, Enum):
    """Escalation severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class EscalationState(str, Enum):
    """Escalation state machine states"""
    TRIGGERED = "triggered"
    NOTIFIED = "notified"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED_FALLBACK = "escalated_fallback"


# SLA timeouts by severity
SLA_TIMEOUTS = {
    EscalationLevel.EMERGENCY: timedelta(minutes=2),
    EscalationLevel.HIGH: timedelta(minutes=5),
    EscalationLevel.MEDIUM: timedelta(minutes=15),
    EscalationLevel.LOW: timedelta(minutes=30),
}


class EscalationNotificationService:
    """Service for handling escalation notifications with state machine tracking"""
    
    # Notification retry settings
    MAX_SMS_RETRIES = 3
    SMS_RETRY_DELAY_SECONDS = 30
    
    async def create_escalation(
        self,
        db: Session,
        business_id: int,
        trigger_type: str,
        reason: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
        escalation_level: EscalationLevel = EscalationLevel.MEDIUM
    ) -> Escalation:
        """Create an escalation record with state machine initialized"""
        
        # Calculate SLA deadline
        sla_deadline = datetime.now(timezone.utc) + SLA_TIMEOUTS.get(escalation_level, timedelta(minutes=15))
        
        escalation = Escalation(
            business_id=business_id,
            call_session_id=session_id,
            state=EscalationState.TRIGGERED.value,
            trigger_type=trigger_type,
            severity=escalation_level.value,
            reason=reason,
            context=context,
            customer_phone=customer_phone,
            customer_name=customer_name,
            sla_deadline=sla_deadline,
            sla_breached=False
        )
        
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        
        logger.info(f"Created escalation {escalation.id} for business {business_id}: {trigger_type}")
        return escalation
    
    async def notify_escalation(
        self,
        db: Session,
        business_id: int,
        trigger_type: str,
        reason: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        escalation_level: EscalationLevel = EscalationLevel.MEDIUM
    ) -> Dict[str, Any]:
        """
        Main entry point for escalation notifications.
        
        Creates escalation record and sends notifications via multiple channels.
        """
        # Get business and emergency contacts
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"success": False, "error": "Business not found"}
        
        # Create escalation record
        escalation = await self.create_escalation(
            db=db,
            business_id=business_id,
            trigger_type=trigger_type,
            reason=reason,
            context=context,
            session_id=session_id,
            customer_phone=customer_phone,
            escalation_level=escalation_level
        )
        
        results = {
            "success": True,
            "escalation_id": escalation.id,
            "business_id": business_id,
            "trigger_type": trigger_type,
            "escalation_level": escalation_level.value,
            "notifications_sent": [],
            "errors": []
        }
        
        # Build notification payload
        notification_data = {
            "escalation_id": escalation.id,
            "business_id": business_id,
            "business_name": business.name,
            "trigger_type": trigger_type,
            "reason": reason,
            "session_id": session_id,
            "customer_phone": customer_phone,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "escalation_level": escalation_level.value,
            "sla_deadline": escalation.sla_deadline.isoformat() if escalation.sla_deadline else None,
            **context
        }
        
        # Determine notification priority
        priority = self._get_notification_priority(escalation_level)
        
        # Track who was notified
        notified_contacts = []
        notification_channels = []
        
        # 1. Trigger webhook first (async, non-blocking)
        webhook_task = asyncio.create_task(
            self._trigger_webhook(db, business_id, notification_data)
        )
        
        # 2. Send SMS to emergency contact if configured
        if business.emergency_contact_phone:
            sms_result = await self._send_escalation_sms(
                to_number=business.emergency_contact_phone,
                contact_name=business.emergency_contact_name,
                business_name=business.name,
                trigger_type=trigger_type,
                reason=reason,
                customer_phone=customer_phone,
                priority=priority
            )
            results["notifications_sent"].append({
                "channel": "sms",
                "recipient": business.emergency_contact_phone,
                "success": sms_result.get("success", False),
                "message_sid": sms_result.get("message_sid")
            })
            if sms_result.get("success"):
                notified_contacts.append({
                    "name": business.emergency_contact_name,
                    "phone": business.emergency_contact_phone,
                    "type": "primary"
                })
                notification_channels.append("sms")
            else:
                results["errors"].append(f"SMS failed: {sms_result.get('error')}")
        
        # 3. Send push notification to business owner
        push_result = await self._send_escalation_push(
            db=db,
            business_id=business_id,
            notification_data=notification_data,
            escalation_level=escalation_level
        )
        results["notifications_sent"].append({
            "channel": "push",
            "success": push_result.get("success", False)
        })
        if push_result.get("success"):
            notification_channels.append("push")
        
        # 4. If primary contact not configured or failed, try fallback
        if not business.emergency_contact_phone and business.fallback_contact_phone:
            logger.info(f"Primary contact not configured, using fallback for business {business_id}")
            sms_result = await self._send_escalation_sms(
                to_number=business.fallback_contact_phone,
                contact_name=business.fallback_contact_name,
                business_name=business.name,
                trigger_type=trigger_type,
                reason=reason,
                customer_phone=customer_phone,
                priority=priority,
                is_fallback=True
            )
            results["notifications_sent"].append({
                "channel": "sms_fallback",
                "recipient": business.fallback_contact_phone,
                "success": sms_result.get("success", False)
            })
            if sms_result.get("success"):
                notified_contacts.append({
                    "name": business.fallback_contact_name,
                    "phone": business.fallback_contact_phone,
                    "type": "fallback"
                })
                notification_channels.append("sms")
        
        # 5. Send email if configured
        if business.emergency_contact_email:
            email_result = await self._send_escalation_email(
                to_email=business.emergency_contact_email,
                contact_name=business.emergency_contact_name,
                business_name=business.name,
                trigger_type=trigger_type,
                reason=reason,
                customer_phone=customer_phone,
                escalation_level=escalation_level
            )
            results["notifications_sent"].append({
                "channel": "email",
                "recipient": business.emergency_contact_email,
                "success": email_result.get("success", False)
            })
            if email_result.get("success"):
                notification_channels.append("email")
        
        # Wait for webhook to complete
        try:
            webhook_result = await asyncio.wait_for(webhook_task, timeout=5.0)
            results["notifications_sent"].append({
                "channel": "webhook",
                "success": webhook_result.get("sent", 0) > 0
            })
            if webhook_result.get("sent", 0) > 0:
                notification_channels.append("webhook")
        except asyncio.TimeoutError:
            results["errors"].append("Webhook timeout")
        
        # Update escalation record with notification info
        escalation.state = EscalationState.NOTIFIED.value
        escalation.notified_contacts = notified_contacts
        escalation.notification_channels = notification_channels
        db.commit()
        
        logger.info(f"Escalation {escalation.id} notified for business {business_id}")
        
        return results
    
    async def acknowledge_escalation(
        self,
        db: Session,
        escalation_id: int,
        acknowledged_by: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition escalation to acknowledged state"""
        
        escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        
        if not escalation:
            return {"success": False, "error": "Escalation not found"}
        
        if escalation.state == EscalationState.RESOLVED.value:
            return {"success": False, "error": "Cannot acknowledge a resolved escalation"}
        
        escalation.state = EscalationState.ACKNOWLEDGED.value
        escalation.acknowledged_by = acknowledged_by
        escalation.acknowledged_at = datetime.now(timezone.utc)
        escalation.acknowledgment_notes = notes
        db.commit()
        
        # Trigger webhook
        await webhook_service.trigger_event(
            event_type="escalation.acknowledged",
            payload={
                "escalation_id": escalation_id,
                "acknowledged_by": acknowledged_by,
                "notes": notes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            business_id=escalation.business_id,
            db=db
        )
        
        logger.info(f"Escalation {escalation_id} acknowledged by user {acknowledged_by}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "state": escalation.state,
            "acknowledged_at": escalation.acknowledged_at.isoformat()
        }
    
    async def resolve_escalation(
        self,
        db: Session,
        escalation_id: int,
        resolved_by: int,
        resolution_action: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition escalation to resolved state"""
        
        escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        
        if not escalation:
            return {"success": False, "error": "Escalation not found"}
        
        escalation.state = EscalationState.RESOLVED.value
        escalation.resolved_by = resolved_by
        escalation.resolved_at = datetime.now(timezone.utc)
        escalation.resolution_action = resolution_action
        escalation.resolution_notes = notes
        db.commit()
        
        # Trigger webhook
        await webhook_service.trigger_event(
            event_type="escalation.resolved",
            payload={
                "escalation_id": escalation_id,
                "resolved_by": resolved_by,
                "resolution_action": resolution_action,
                "notes": notes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            business_id=escalation.business_id,
            db=db
        )
        
        logger.info(f"Escalation {escalation_id} resolved by user {resolved_by}: {resolution_action}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "state": escalation.state,
            "resolution_action": resolution_action,
            "resolved_at": escalation.resolved_at.isoformat()
        }
    
    async def escalate_to_fallback(
        self,
        db: Session,
        escalation_id: int
    ) -> Dict[str, Any]:
        """Escalate to fallback contact when primary is unresponsive"""
        
        escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not escalation:
            return {"success": False, "error": "Escalation not found"}
        
        business = db.query(Business).filter(Business.id == escalation.business_id).first()
        if not business or not business.fallback_contact_phone:
            return {"success": False, "error": "No fallback contact configured"}
        
        # Mark SLA as breached
        escalation.sla_breached = True
        escalation.state = EscalationState.ESCALATED_FALLBACK.value
        db.commit()
        
        # Send notification to fallback
        priority = self._get_notification_priority(EscalationLevel(escalation.severity))
        sms_result = await self._send_escalation_sms(
            to_number=business.fallback_contact_phone,
            contact_name=business.fallback_contact_name,
            business_name=business.name,
            trigger_type=escalation.trigger_type,
            reason=escalation.reason,
            customer_phone=escalation.customer_phone,
            priority=priority,
            is_fallback=True
        )
        
        logger.warning(f"Escalation {escalation_id} escalated to fallback contact")
        
        return {
            "success": sms_result.get("success", False),
            "escalation_id": escalation_id,
            "state": escalation.state,
            "fallback_contact": business.fallback_contact_phone
        }
    
    def get_pending_escalations(
        self,
        db: Session,
        business_id: Optional[int] = None,
        states: Optional[List[str]] = None
    ) -> List[Escalation]:
        """Get pending escalations for supervisor dashboard"""
        
        query = db.query(Escalation)
        
        if business_id:
            query = query.filter(Escalation.business_id == business_id)
        
        if states:
            query = query.filter(Escalation.state.in_(states))
        else:
            # By default, show non-resolved escalations
            query = query.filter(Escalation.state != EscalationState.RESOLVED.value)
        
        return query.order_by(Escalation.created_at.desc()).all()
    
    def check_sla_breaches(self, db: Session) -> List[Escalation]:
        """Check for SLA breaches and mark them"""
        
        now = datetime.now(timezone.utc)
        
        breached = db.query(Escalation).filter(
            Escalation.state.in_([
                EscalationState.TRIGGERED.value,
                EscalationState.NOTIFIED.value
            ]),
            Escalation.sla_deadline < now,
            Escalation.sla_breached == False
        ).all()
        
        for escalation in breached:
            escalation.sla_breached = True
            logger.warning(f"SLA breach detected for escalation {escalation.id}")
        
        if breached:
            db.commit()
        
        return breached
    
    async def _send_escalation_sms(
        self,
        to_number: str,
        contact_name: str,
        business_name: str,
        trigger_type: str,
        reason: str,
        customer_phone: Optional[str],
        priority: str,
        is_fallback: bool = False
    ) -> Dict[str, Any]:
        """Send escalation SMS notification"""
        
        # Build message based on priority
        if priority == "emergency":
            prefix = "🚨 EMERGENCY ALERT"
        elif priority == "urgent":
            prefix = "⚠️ URGENT"
        else:
            prefix = "📞 Escalation"
        
        fallback_note = " (PRIMARY UNRESPONSIVE)" if is_fallback else ""
        customer_info = f"Customer: {customer_phone}" if customer_phone else ""
        
        message = (
            f"{prefix}{fallback_note}\n"
            f"Business: {business_name}\n"
            f"Type: {trigger_type}\n"
            f"Reason: {reason}\n"
            f"{customer_info}\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"Please respond immediately or call the customer back."
        )
        
        return await sms_service.send_sms(to_number, message)
    
    async def _send_escalation_push(
        self,
        db: Session,
        business_id: int,
        notification_data: Dict[str, Any],
        escalation_level: EscalationLevel
    ) -> Dict[str, Any]:
        """Send push notification for escalation"""
        
        # Determine notification type based on level
        if escalation_level == EscalationLevel.EMERGENCY:
            notification_type = NotificationType.EMERGENCY_ALERT
        else:
            notification_type = NotificationType.HUMAN_INTERVENTION_REQUIRED
        
        return await mobile_app_service.send_business_notification(
            db=db,
            business_id=business_id,
            notification_type=notification_type,
            data=notification_data
        )
    
    async def _send_escalation_email(
        self,
        to_email: str,
        contact_name: str,
        business_name: str,
        trigger_type: str,
        reason: str,
        customer_phone: Optional[str],
        escalation_level: EscalationLevel
    ) -> Dict[str, Any]:
        """Send escalation email notification"""
        try:
            from app.services.email_service import EmailService
            
            email_service = EmailService()
            
            subject = f"[{escalation_level.value.upper()}] Human Intervention Required - {business_name}"
            
            body = f"""
Hello {contact_name or 'Manager'},

An escalation has been triggered that requires your immediate attention.

BUSINESS: {business_name}
TRIGGER TYPE: {trigger_type}
SEVERITY: {escalation_level.value.upper()}
REASON: {reason}
CUSTOMER PHONE: {customer_phone or 'N/A'}
TIME: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Please take action immediately by:
1. Calling the customer back
2. Using the manager dashboard to approve/reject the AI's action
3. Transferring the call to a human agent

This is an automated notification from your AI Receptionist.

---
Receptium AI Receptionist
"""
            
            # Email service is synchronous, run in thread pool
            result = await asyncio.to_thread(
                email_service.send_email,
                to_email=to_email,
                subject=subject,
                body=body
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send escalation email: {e}")
            return {"success": False, "error": str(e)}
    
    async def _trigger_webhook(
        self,
        db: Session,
        business_id: int,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger webhook for escalation event"""
        return await webhook_service.trigger_event(
            event_type="escalation.triggered",
            payload=payload,
            business_id=business_id,
            db=db
        )
    
    def _get_notification_priority(self, escalation_level: EscalationLevel) -> str:
        """Map escalation level to notification priority"""
        mapping = {
            EscalationLevel.LOW: "normal",
            EscalationLevel.MEDIUM: "normal",
            EscalationLevel.HIGH: "urgent",
            EscalationLevel.EMERGENCY: "emergency"
        }
        return mapping.get(escalation_level, "normal")


# Singleton instance
escalation_service = EscalationNotificationService()
