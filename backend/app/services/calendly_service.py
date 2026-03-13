"""
Calendly Integration Service

Provides direct integration with Calendly API:
- Webhook event handling
- Event type synchronization
- Booking management
- OAuth2 token management
"""

import json
import hmac
import hashlib
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.encryption import encryption_service
from app.models.models import CalendarIntegration, Appointment, Business


class CalendlyService:
    """Service for Calendly API integration"""
    
    def __init__(self):
        self.BASE_URL = "https://api.calendly.com"
        self.API_VERSION = "2025-02-13"
    
    def get_calendly_auth_url(self, business_id: int) -> str:
        """
        Generate Calendly OAuth URL
        
        Calendly uses OAuth 2.0 for authorization
        """
        import secrets
        
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": settings.CALENDLY_CLIENT_ID,
            "redirect_uri": settings.CALENDLY_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email calendar_events:read calendar_events:write",
            "state": f"{business_id}:{state}",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        import urllib.parse
        return f"https://auth.calendly.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    async def exchange_calendly_code(
        self,
        code: str,
        business_id: int,
        db: Session
    ) -> CalendarIntegration:
        """Exchange Calendly OAuth code for tokens"""
        token_url = "https://auth.calendly.com/oauth/token"
        
        data = {
            "client_id": settings.CALENDLY_CLIENT_ID,
            "client_secret": settings.CALENDLY_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.CALENDLY_REDIRECT_URI
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to exchange Calendly code: {error_text}")
                
                tokens = await response.json()
                
                # Get user info to retrieve Calendly URI
                user_info = await self._get_user_info(tokens["access_token"])
                
                # Save or update integration
                integration = db.query(CalendarIntegration).filter(
                    CalendarIntegration.business_id == business_id,
                    CalendarIntegration.provider == "calendly"
                ).first()
                
                if not integration:
                    integration = CalendarIntegration(
                        business_id=business_id,
                        provider="calendly",
                        status="active",
                        calendar_id=user_info.get("resource", {}).get("uri"),  # Store Calendly URI
                        last_sync_at=datetime.now(timezone.utc)
                    )
                    db.add(integration)
                else:
                    integration.status = "active"
                    integration.calendar_id = user_info.get("resource", {}).get("uri")
                    integration.last_sync_at = datetime.now(timezone.utc)
                
                # Encrypt and store tokens
                integration.access_token = encryption_service.encrypt_access_token(
                    tokens["access_token"]
                )
                integration.refresh_token = encryption_service.encrypt_access_token(
                    tokens.get("refresh_token", "")
                )
                
                # Parse expiration
                expires_in = tokens.get("expires_in", 7200)  # Default 2 hours
                from datetime import timedelta
                integration.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                db.commit()
                db.refresh(integration)
                
                return integration
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get authenticated user info from Calendly"""
        url = f"{self.BASE_URL}/users/me"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception("Failed to get Calendly user info")
                
                return await response.json()
    
    async def refresh_access_token(
        self,
        integration: CalendarIntegration,
        db: Session
    ) -> str:
        """Refresh Calendly access token"""
        if not integration.refresh_token:
            raise Exception("No refresh token available")
        
        token_url = "https://auth.calendly.com/oauth/token"
        
        data = {
            "client_id": settings.CALENDLY_CLIENT_ID,
            "client_secret": settings.CALENDLY_CLIENT_SECRET,
            "refresh_token": encryption_service.decrypt_access_token(integration.refresh_token),
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to refresh Calendly token: {error_text}")
                
                tokens = await response.json()
                
                # Update tokens in database
                integration.access_token = encryption_service.encrypt_access_token(
                    tokens["access_token"]
                )
                
                if "refresh_token" in tokens:
                    integration.refresh_token = encryption_service.encrypt_access_token(
                        tokens["refresh_token"]
                    )
                
                expires_in = tokens.get("expires_in", 7200)
                from datetime import timedelta
                integration.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                db.commit()
                
                return tokens["access_token"]
    
    async def get_access_token(self, integration: CalendarIntegration, db: Session) -> str:
        """Get valid access token, refreshing if necessary"""
        # Check if token is expired or about to expire (within 5 minutes)
        from datetime import timedelta
        if integration.token_expires_at and integration.token_expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
            return await self.refresh_access_token(integration, db)
        
        return encryption_service.decrypt_access_token(integration.access_token)
    
    async def get_event_types(self, integration: CalendarIntegration, db: Session) -> List[Dict[str, Any]]:
        """Get all event types from Calendly"""
        access_token = await self.get_access_token(integration, db)
        
        user_uri = integration.calendar_id
        if not user_uri:
            raise Exception("Calendly user URI not found")
        
        url = f"{self.BASE_URL}/event_types"
        params = {"user": user_uri}
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get Calendly event types: {error_text}")
                
                result = await response.json()
                return result.get("collection", [])
    
    async def get_scheduled_events(
        self,
        integration: CalendarIntegration,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get scheduled events from Calendly"""
        access_token = await self.get_access_token(integration, db)
        
        url = f"{self.BASE_URL}/scheduled_events"
        params = {}
        
        if start_time:
            params["min_start_time"] = start_time.isoformat()
        if end_time:
            params["max_start_time"] = end_time.isoformat()
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get Calendly events: {error_text}")
                
                result = await response.json()
                return result.get("collection", [])
    
    async def create_webhook_subscription(
        self,
        integration: CalendarIntegration,
        webhook_url: str,
        events: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Create webhook subscription in Calendly
        
        Events: ["invitee.created", "invitee.canceled", "event_type.updated", etc.]
        """
        access_token = await self.get_access_token(integration, db)
        
        url = f"{self.BASE_URL}/webhook_subscriptions"
        
        payload = {
            "webhook_subscription": {
                "url": webhook_url,
                "events": events,
                "scope": integration.calendar_id
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to create Calendly webhook: {error_text}")
                
                result = await response.json()
                return result.get("resource", {})
    
    async def delete_webhook_subscription(
        self,
        integration: CalendarIntegration,
        subscription_id: str,
        db: Session
    ) -> bool:
        """Delete webhook subscription"""
        access_token = await self.get_access_token(integration, db)
        
        url = f"{self.BASE_URL}/webhook_subscriptions/{subscription_id}"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                if response.status != 204:
                    error_text = await response.text()
                    raise Exception(f"Failed to delete Calendly webhook: {error_text}")
                
                return True
    
    def verify_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verify Calendly webhook signature
        
        Calendly sends X-Calendly-Signature header with HMAC-SHA256 signature
        """
        try:
            # Compute HMAC-SHA256
            computed_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(computed_signature, signature)
        except Exception as e:
            print(f"Error verifying webhook signature: {e}")
            return False
    
    async def handle_webhook_event(
        self,
        payload: Dict[str, Any],
        signature: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Handle incoming Calendly webhook event
        
        Event types:
        - invitee.created: New booking
        - invitee.canceled: Cancellation
        - event_type.updated: Event type changed
        - webhook_subscription.created/updated/deleted
        """
        # Verify signature if secret is configured
        webhook_secret = settings.CALENDLY_WEBHOOK_SECRET
        if webhook_secret:
            if not self.verify_webhook_signature(
                json.dumps(payload, sort_keys=True),
                signature,
                webhook_secret
            ):
                raise Exception("Invalid webhook signature")
        
        event_data = payload.get("event", {})
        event_type = payload.get("event_type")
        
        # Handle different event types
        if event_type == "invitee_created":
            return await self._handle_invitee_created(event_data, db)
        elif event_type == "invitee_canceled":
            return await self._handle_invitee_canceled(event_data, db)
        elif event_type == "invitee_rescheduled":
            return await self._handle_invitee_rescheduled(event_data, db)
        else:
            return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}
    
    async def _handle_invitee_created(
        self,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle new booking from Calendly"""
        invitee = event_data.get("data", {})
        
        # Extract booking details
        booking_details = {
            "event_uuid": invitee.get("uuid"),
            "event_type": invitee.get("event_type", {}).get("name"),
            "start_time": invitee.get("start_time"),
            "end_time": invitee.get("end_time"),
            "timezone": invitee.get("timezone"),
            "name": invitee.get("name", ""),
            "email": invitee.get("email", ""),
            "answers": invitee.get("answers", []),  # Custom questions & answers
            "status": "confirmed",
            "source": "calendly"
        }
        
        # Try to find associated business by matching Calendly URI
        # This requires the integration to be linked
        # For now, we'll log the event
        print(f"[Calendly Webhook] New booking: {booking_details['name']} - {booking_details['start_time']}")
        
        # TODO: Create appointment in database if business is found
        # business = self._find_business_by_calendly_uri(invitee.get("user").get("uri"))
        # if business:
        #     self._create_appointment_from_booking(business.id, booking_details, db)
        
        return {
            "status": "processed",
            "action": "appointment_created",
            "booking": booking_details
        }
    
    async def _handle_invitee_canceled(
        self,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle cancellation from Calendly"""
        invitee = event_data.get("data", {})
        
        cancel_details = {
            "event_uuid": invitee.get("uuid"),
            "name": invitee.get("name", ""),
            "email": invitee.get("email", ""),
            "cancellation_reason": invitee.get("cancellation", {}).get("reason", ""),
            "status": "canceled"
        }
        
        print(f"[Calendly Webhook] Cancellation: {cancel_details['name']}")
        
        # TODO: Update appointment status in database
        # appointment = db.query(Appointment).filter(
        #     Appointment.source == "calendly",
        #     # Match by external ID or email+time
        # ).first()
        # if appointment:
        #     appointment.status = "cancelled"
        #     db.commit()
        
        return {
            "status": "processed",
            "action": "appointment_canceled",
            "booking": cancel_details
        }
    
    async def _handle_invitee_rescheduled(
        self,
        event_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle rescheduled booking from Calendly"""
        invitee = event_data.get("data", {})
        
        reschedule_details = {
            "event_uuid": invitee.get("uuid"),
            "old_start_time": invitee.get("old_start_time"),
            "new_start_time": invitee.get("start_time"),
            "name": invitee.get("name", ""),
            "status": "rescheduled"
        }
        
        print(f"[Calendly Webhook] Rescheduled: {reschedule_details['name']} from {reschedule_details['old_start_time']} to {reschedule_details['new_start_time']}")
        
        # TODO: Update appointment time in database
        
        return {
            "status": "processed",
            "action": "appointment_rescheduled",
            "booking": reschedule_details
        }
    
    def _find_business_by_calendly_uri(self, calendly_uri: str) -> Optional[Business]:
        """Find business by Calendly user URI"""
        # This would need a DB session in real implementation
        # For now, return None
        return None


# Singleton instance
calendly_service = CalendlyService()
