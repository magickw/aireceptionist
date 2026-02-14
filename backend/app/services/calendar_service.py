"""
Calendar Integration Service

Supports:
- Google Calendar OAuth2
- Outlook Calendar
- Event sync (both ways)
"""

import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import CalendarIntegration


class CalendarService:
    """Service for calendar integrations"""
    
    # Google OAuth config (should be in settings in production)
    GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID if hasattr(settings, 'GOOGLE_CLIENT_ID') else None
    GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET if hasattr(settings, 'GOOGLE_CLIENT_SECRET') else None
    GOOGLE_REDIRECT_URI = "https://your-domain.com/api/calendar/google/callback"
    
    # Microsoft OAuth config
    MICROSOFT_CLIENT_ID = settings.MICROSOFT_CLIENT_ID if hasattr(settings, 'MICROSOFT_CLIENT_ID') else None
    MICROSOFT_CLIENT_SECRET = settings.MICROSOFT_CLIENT_SECRET if hasattr(settings, 'MICROSOFT_CLIENT_SECRET') else None
    MICROSOFT_REDIRECT_URI = "https://your-domain.com/api/calendar/microsoft/callback"
    
    def get_google_auth_url(self, business_id: int) -> str:
        """Generate Google OAuth URL"""
        import secrets
        
        # Generate state for security
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.GOOGLE_CLIENT_ID,
            "redirect_uri": self.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar",
            "access_type": "offline",
            "state": f"{business_id}:{state}"
        }
        
        import urllib.parse
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    def get_microsoft_auth_url(self, business_id: int) -> str:
        """Generate Microsoft OAuth URL"""
        import secrets
        
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.MICROSOFT_CLIENT_ID,
            "redirect_uri": self.MICROSOFT_REDIRECT_URI,
            "response_type": "code",
            "scope": "https://graph.microsoft.com/Calendars.ReadWrite offline_access",
            "state": f"{business_id}:{state}"
        }
        
        import urllib.parse
        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    
    async def exchange_google_code(
        self,
        code: str,
        business_id: int,
        db: Session
    ) -> CalendarIntegration:
        """Exchange Google OAuth code for tokens"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.GOOGLE_CLIENT_ID,
            "client_secret": self.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.GOOGLE_REDIRECT_URI
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    raise Exception("Failed to exchange Google code")
                
                tokens = await response.json()
                
                # Get primary calendar
                async with session.get(
                    "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"}
                ) as cal_response:
                    calendars = await cal_response.json()
                    primary_cal = next(
                        (c for c in calendars.get("items", []) if c.get("primary")),
                        None
                    )
                    calendar_id = primary_cal.get("id") if primary_cal else "primary"
                
                # Store or update integration
                integration = db.query(CalendarIntegration).filter(
                    CalendarIntegration.business_id == business_id,
                    CalendarIntegration.provider == "google"
                ).first()
                
                if integration:
                    integration.access_token = tokens["access_token"]
                    integration.refresh_token = tokens.get("refresh_token")
                    integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
                    integration.calendar_id = calendar_id
                    integration.status = "active"
                else:
                    integration = CalendarIntegration(
                        business_id=business_id,
                        provider="google",
                        access_token=tokens["access_token"],
                        refresh_token=tokens.get("refresh_token"),
                        token_expires_at=datetime.utcnow() + timedelta(seconds=tokens["expires_in"]),
                        calendar_id=calendar_id,
                        status="active"
                    )
                    db.add(integration)
                
                db.commit()
                db.refresh(integration)
                return integration
    
    async def refresh_google_token(
        self,
        integration: CalendarIntegration,
        db: Session
    ) -> bool:
        """Refresh Google access token"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.GOOGLE_CLIENT_ID,
            "client_secret": self.GOOGLE_CLIENT_SECRET,
            "refresh_token": integration.refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    integration.status = "expired"
                    db.commit()
                    return False
                
                tokens = await response.json()
                
                integration.access_token = tokens["access_token"]
                integration.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=tokens.get("expires_in", 3600)
                )
                integration.status = "active"
                db.commit()
                return True
    
    async def create_calendar_event(
        self,
        integration: CalendarIntegration,
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create an event on the calendar"""
        # Check token validity
        if integration.token_expires_at and integration.token_expires_at < datetime.utcnow():
            if not await self.refresh_google_token(integration, db):
                raise Exception("Failed to refresh calendar token")
        
        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            }
        }
        
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        
        headers = {
            "Authorization": f"Bearer {integration.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/{integration.calendar_id}/events"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=event, headers=headers) as response:
                if response.status not in (200, 201):
                    raise Exception(f"Failed to create calendar event: {await response.text()}")
                
                return await response.json()
    
    async def get_calendar_events(
        self,
        integration: CalendarIntegration,
        start_date: datetime,
        end_date: datetime,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get events from the calendar"""
        # Check token validity
        if integration.token_expires_at and integration.token_expires_at < datetime.utcnow():
            if not await self.refresh_google_token(integration, db):
                raise Exception("Failed to refresh calendar token")
        
        headers = {
            "Authorization": f"Bearer {integration.access_token}"
        }
        
        params = {
            "timeMin": start_date.isoformat(),
            "timeMax": end_date.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime"
        }
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/{integration.calendar_id}/events"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get calendar events: {await response.text()}")
                
                data = await response.json()
                return data.get("items", [])
    
    def list_integrations(
        self,
        business_id: int,
        db: Session
    ) -> List[CalendarIntegration]:
        """List all calendar integrations for a business"""
        return db.query(CalendarIntegration).filter(
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.status == "active"
        ).all()
    
    def get_integration(
        self,
        integration_id: int,
        business_id: int,
        db: Session
    ) -> Optional[CalendarIntegration]:
        """Get a specific calendar integration"""
        return db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.business_id == business_id
        ).first()
    
    def delete_integration(
        self,
        integration_id: int,
        business_id: int,
        db: Session
    ) -> bool:
        """Delete a calendar integration"""
        integration = self.get_integration(integration_id, business_id, db)
        if not integration:
            return False
        
        db.delete(integration)
        db.commit()
        return True


# Singleton instance
calendar_service = CalendarService()
