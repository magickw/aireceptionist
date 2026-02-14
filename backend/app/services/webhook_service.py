"""
Webhook Service for Event Notifications

Handles:
- Webhook CRUD operations
- Event triggering and delivery
- Signature verification
- Retry logic
"""

import hmac
import hashlib
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models.models import Webhook


class WebhookService:
    """Service for managing and triggering webhooks"""
    
    # Supported event types
    EVENT_TYPES = [
        "call.started",
        "call.ended",
        "call.voicemail",
        "call.completed",
        "appointment.created",
        "appointment.updated",
        "appointment.cancelled",
        "appointment.completed",
        "customer.new",
        "customer.churn_risk",
        "automation.started",
        "automation.completed",
        "automation.failed"
    ]
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # seconds
    
    def create_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected = self.create_signature(payload, secret)
        return hmac.compare_digest(expected, signature)
    
    def list_webhooks(
        self,
        business_id: int,
        db: Session,
        status: Optional[str] = None
    ) -> List[Webhook]:
        """List all webhooks for a business"""
        query = db.query(Webhook).filter(Webhook.business_id == business_id)
        if status:
            query = query.filter(Webhook.status == status)
        return query.order_by(desc(Webhook.created_at)).all()
    
    def get_webhook(
        self,
        webhook_id: int,
        business_id: int,
        db: Session
    ) -> Optional[Webhook]:
        """Get a specific webhook"""
        return db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.business_id == business_id
        ).first()
    
    def create_webhook(
        self,
        business_id: int,
        name: str,
        url: str,
        events: List[str],
        db: Session,
        secret: Optional[str] = None
    ) -> Webhook:
        """Create a new webhook"""
        # Validate events
        invalid_events = [e for e in events if e not in self.EVENT_TYPES]
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}")
        
        # Generate secret if not provided
        if not secret:
            import secrets
            secret = secrets.token_hex(32)
        
        webhook = Webhook(
            business_id=business_id,
            name=name,
            url=url,
            events=events,
            secret=secret,
            status="active"
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        return webhook
    
    def update_webhook(
        self,
        webhook_id: int,
        business_id: int,
        db: Session,
        **updates
    ) -> Optional[Webhook]:
        """Update a webhook"""
        webhook = self.get_webhook(webhook_id, business_id, db)
        if not webhook:
            return None
        
        for key, value in updates.items():
            if hasattr(webhook, key) and value is not None:
                setattr(webhook, key, value)
        
        db.commit()
        db.refresh(webhook)
        return webhook
    
    def delete_webhook(
        self,
        webhook_id: int,
        business_id: int,
        db: Session
    ) -> bool:
        """Delete a webhook"""
        webhook = self.get_webhook(webhook_id, business_id, db)
        if not webhook:
            return False
        
        db.delete(webhook)
        db.commit()
        return True
    
    async def trigger_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        business_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Trigger an event to all matching webhooks.
        
        Returns:
            Dict with success count and failures
        """
        # Get all active webhooks for this business that subscribe to this event
        webhooks = db.query(Webhook).filter(
            Webhook.business_id == business_id,
            Webhook.status == "active"
        ).all()
        
        # Filter webhooks that subscribe to this event type
        matching_webhooks = [
            w for w in webhooks
            if event_type in w.events or "*" in w.events
        ]
        
        results = {
            "event": event_type,
            "total_webhooks": len(matching_webhooks),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        # Trigger each webhook
        for webhook in matching_webhooks:
            success = await self._deliver_webhook(webhook, event_type, payload, db)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any],
        db: Session
    ) -> bool:
        """Deliver a webhook with retry logic"""
        payload_str = json.dumps(payload, default=str)
        signature = self.create_signature(payload_str, webhook.secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": str(webhook.id)
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status < 400:
                            # Success - update webhook stats
                            webhook.last_triggered_at = datetime.utcnow()
                            webhook.failure_count = 0
                            db.commit()
                            return True
                        elif response.status >= 500:
                            # Server error - retry
                            await asyncio.sleep(self.retry_delays[attempt])
                            continue
                        else:
                            # Client error - don't retry
                            break
                            
            except Exception as e:
                print(f"Webhook delivery error: {e}")
                await asyncio.sleep(self.retry_delays[attempt])
        
        # Failed - update failure count
        webhook.failure_count += 1
        if webhook.failure_count >= 5:
            webhook.status = "failed"
        db.commit()
        return False
    
    def get_available_events(self) -> List[str]:
        """Get list of available event types"""
        return self.EVENT_TYPES


# Singleton instance
webhook_service = WebhookService()
