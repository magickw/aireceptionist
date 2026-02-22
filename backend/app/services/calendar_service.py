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
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import CalendarIntegration, Appointment, Business


class CalendarService:
    """Service for calendar integrations"""
    
    def __init__(self):
        # Google OAuth config (instance attributes for testability)
        self.GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
        self.GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
        self.GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
        
        # Microsoft OAuth config (instance attributes for testability)
        self.MICROSOFT_CLIENT_ID = settings.MICROSOFT_CLIENT_ID
        self.MICROSOFT_CLIENT_SECRET = settings.MICROSOFT_CLIENT_SECRET
        self.MICROSOFT_REDIRECT_URI = settings.MICROSOFT_REDIRECT_URI
    
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
        return f"https://accounts.google.com/o/oauth2/v2.0/auth?{urllib.parse.urlencode(params)}"
    
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
    
    async def check_availability(
        self,
        integration: CalendarIntegration,
        start_time: datetime,
        end_time: datetime,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Check if a time slot is available using Google Calendar freebusy API.
        
        Returns:
            {
                "available": bool,
                "conflicts": List of conflicting events,
                "busy_periods": List of busy time ranges
            }
        """
        # Check token validity
        if integration.token_expires_at and integration.token_expires_at < datetime.utcnow():
            if not await self.refresh_google_token(integration, db):
                raise Exception("Failed to refresh calendar token")
        
        headers = {
            "Authorization": f"Bearer {integration.access_token}",
            "Content-Type": "application/json"
        }
        
        # Use freebusy API for efficient availability checking
        body = {
            "timeMin": start_time.isoformat(),
            "timeMax": end_time.isoformat(),
            "items": [{"id": integration.calendar_id}]
        }
        
        url = "https://www.googleapis.com/calendar/v3/freeBusy"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers) as response:
                if response.status != 200:
                    # Fallback to checking events directly
                    return await self._check_availability_via_events(
                        integration, start_time, end_time, db
                    )
                
                data = await response.json()
                calendars = data.get("calendars", {})
                calendar_data = calendars.get(integration.calendar_id, {})
                busy_periods = calendar_data.get("busy", [])
                
                # Check if any busy period overlaps with our requested slot
                conflicts = []
                for period in busy_periods:
                    busy_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
                    busy_end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
                    
                    # Check for overlap
                    if start_time < busy_end and end_time > busy_start:
                        conflicts.append({
                            "start": busy_start.isoformat(),
                            "end": busy_end.isoformat()
                        })
                
                return {
                    "available": len(conflicts) == 0,
                    "conflicts": conflicts,
                    "busy_periods": busy_periods
                }
    
    async def _check_availability_via_events(
        self,
        integration: CalendarIntegration,
        start_time: datetime,
        end_time: datetime,
        db: Session = None
    ) -> Dict[str, Any]:
        """Fallback availability check using events list"""
        events = await self.get_calendar_events(integration, start_time, end_time, db)
        
        conflicts = []
        for event in events:
            event_start = event.get("start", {})
            event_end = event.get("end", {})
            
            # Parse event times
            if "dateTime" in event_start:
                evt_start = datetime.fromisoformat(event_start["dateTime"].replace("Z", "+00:00"))
                evt_end = datetime.fromisoformat(event_end["dateTime"].replace("Z", "+00:00"))
                
                # Check for overlap
                if start_time < evt_end and end_time > evt_start:
                    conflicts.append({
                        "start": evt_start.isoformat(),
                        "end": evt_end.isoformat(),
                        "summary": event.get("summary", "Busy")
                    })
        
        return {
            "available": len(conflicts) == 0,
            "conflicts": conflicts,
            "busy_periods": []
        }
    
    async def get_available_slots(
        self,
        integration: CalendarIntegration,
        date: datetime,
        duration_minutes: int = 60,
        business_hours: tuple = (9, 17),
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a given date.
        
        Args:
            integration: Calendar integration
            date: The date to check
            duration_minutes: Duration of each slot
            business_hours: Tuple of (start_hour, end_hour) in 24h format
            db: Database session
        
        Returns:
            List of available slots with start/end times
        """
        # Define the time range for the day
        day_start = date.replace(hour=business_hours[0], minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=business_hours[1], minute=0, second=0, microsecond=0)
        
        # Get busy periods for the day
        availability = await self.check_availability(integration, day_start, day_end, db)
        busy_periods = availability.get("conflicts", [])
        
        # Generate potential slots
        slots = []
        current = day_start
        while current + timedelta(minutes=duration_minutes) <= day_end:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any busy period
            is_available = True
            for busy in busy_periods:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00").replace("+00:00", ""))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00").replace("+00:00", ""))
                
                if slot_start < busy_end and slot_end > busy_start:
                    is_available = False
                    break
            
            if is_available:
                slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                    "display": slot_start.strftime("%I:%M %p")
                })
            
            current += timedelta(minutes=30)  # 30-minute increments
        
        return slots
    
    def check_db_conflicts(
        self,
        business_id: int,
        start_time: datetime,
        end_time: datetime,
        db: Session,
        service_type: str = None,
        exclude_appointment_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Check for conflicting appointments in the local database.
        
        For hotels, this checks inventory. For others, it checks for any overlap.
        
        Returns list of conflicting appointments.
        """
        from app.models.models import Appointment, MenuItem, Business
        
        business = db.query(Business).filter(Business.id == business_id).first()

        # If business is a hotel and a service_type (room type) is provided
        if business and business.type == 'hotel' and service_type:
            # Find the menu item that represents this room type
            menu_item = db.query(MenuItem).filter(
                MenuItem.business_id == business_id,
                MenuItem.name.ilike(f'%{service_type.split(" Room")[0]}%')
            ).first()

            if menu_item and menu_item.inventory > 0:
                # Count overlapping appointments for this room type
                query = db.query(Appointment).filter(
                    Appointment.business_id == business_id,
                    Appointment.status.in_(["scheduled", "confirmed"]),
                    Appointment.service_type == service_type,
                    Appointment.appointment_time < end_time,
                    (Appointment.appointment_time + timedelta(hours=1)) > start_time # A simple overlap check
                )

                if exclude_appointment_id:
                    query = query.filter(Appointment.id != exclude_appointment_id)

                booked_count = query.count()

                if booked_count >= menu_item.inventory:
                    return [{
                        "id": None,
                        "reason": "inventory_full",
                        "message": f"All {menu_item.inventory} rooms of type '{service_type}' are booked for the selected dates."
                    }]
                else:
                    return [] # Inventory available

        # Original logic for non-hotel businesses or if no service_type is specified
        query = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.status.in_(["scheduled", "confirmed"]),
            Appointment.appointment_time < end_time,
            Appointment.appointment_time >= start_time - timedelta(hours=2)  # Buffer for appointment duration
        )
        
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        
        conflicts = []
        for appt in query.all():
            # Estimate end time (default 1 hour if not stored)
            appt_end = appt.appointment_time + timedelta(hours=1)
            if start_time < appt_end and end_time > appt.appointment_time:
                conflicts.append({
                    "id": appt.id,
                    "customer_name": appt.customer_name,
                    "start": appt.appointment_time.isoformat(),
                    "end": appt_end.isoformat(),
                    "service": appt.service_type,
                    "source": appt.source # Include source for better debugging
                })
        
        return conflicts
    
    async def get_business_availability(
        self,
        business_id: int,
        date: datetime,
        duration_minutes: int = 60,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a given business on a specific date,
        considering operating hours and existing appointments (internal and external).
        """
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business or not business.operating_hours:
            # Default to 9 AM to 5 PM if no operating hours are set
            business_hours = {"start": "09:00", "end": "17:00"}
        else:
            day_of_week = date.strftime('%A').lower() # e.g., 'monday'
            business_hours = business.operating_hours.get(day_of_week, {"start": "09:00", "end": "17:00"})
            
        try:
            start_hour, start_minute = map(int, business_hours["start"].split(':'))
            end_hour, end_minute = map(int, business_hours["end"].split(':'))
        except (KeyError, ValueError):
            start_hour, start_minute = 9, 0
            end_hour, end_minute = 17, 0

        # Define the time range for the day based on operating hours
        day_start = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        day_end = date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        # Ensure we don't go past today's current time for future slots
        if date.date() == datetime.now().date():
            if day_start < datetime.now():
                day_start = datetime.now()
            
        # Get all appointments for the day (internal + external)
        all_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.status.in_(["scheduled", "confirmed"]),
            Appointment.appointment_time >= date.replace(hour=0, minute=0, second=0, microsecond=0),
            Appointment.appointment_time < date.replace(hour=23, minute=59, second=59, microsecond=999999)
        ).all()
        
        # Convert appointments to busy periods
        busy_periods = []
        for appt in all_appointments:
            # Assuming a default appointment duration of 1 hour if not specified
            appt_duration = timedelta(hours=1) 
            # If service_type implies a specific duration, that could be used here
            
            busy_periods.append({
                "start": appt.appointment_time,
                "end": appt.appointment_time + appt_duration
            })

        # Generate potential slots
        slots = []
        current = day_start
        # Ensure 'current' is always at a clean interval (e.g., on the hour or half-hour)
        if current.minute % 30 != 0:
            current = current.replace(minute=(current.minute // 30) * 30, second=0, microsecond=0)
            if current < day_start: # if rounding down went before start_time
                current += timedelta(minutes=30)
                
        while current + timedelta(minutes=duration_minutes) <= day_end:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any busy period
            is_available = True
            for busy in busy_periods:
                if (slot_start < busy["end"] and slot_end > busy["start"]):
                    is_available = False
                    break
            
            if is_available:
                # Only add if the slot is in the future
                if slot_start > datetime.now():
                    slots.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "display": slot_start.strftime("%I:%M %p")
                    })
            
            current += timedelta(minutes=30)  # 30-minute increments
        
        return slots
    
    async def sync_appointment_to_calendar(
        self,
        appointment_id: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Sync an appointment to the connected calendar.
        
        This should be called after an appointment is created in the database.
        
        Returns:
            The created calendar event or None if no calendar connected.
        """
        from app.models.models import Appointment
        
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return None
        
        # Only sync if the appointment source is internal
        if appointment.source != "internal":
            return None
            
        # Get calendar integration for this business
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.business_id == appointment.business_id,
            CalendarIntegration.status == "active"
        ).first()
        
        if not integration:
            return None
        
        # Calculate end time (default 1 hour)
        end_time = appointment.appointment_time + timedelta(hours=1)
        
        # Create event
        summary = f"{appointment.service_type or 'Appointment'} - {appointment.customer_name}"
        description = f"""
Appointment Details:
- Customer: {appointment.customer_name}
- Phone: {appointment.customer_phone}
- Service: {appointment.service_type or 'General'}

Booked via AI Receptionist
        """.strip()
        
        try:
            event = await self.create_calendar_event(
                integration=integration,
                summary=summary,
                description=description,
                start_time=appointment.appointment_time,
                end_time=end_time,
                attendees=None,
                db=db
            )
            
            # Store the calendar event ID with the appointment if we had such a field
            # For now, just return the event
            return event
            
        except Exception as e:
            print(f"[Calendar Service] Failed to sync appointment: {e}")
            return None
    
    async def check_and_book_appointment(
        self,
        business_id: int,
        start_time: datetime,
        end_time: datetime,
        customer_name: str,
        customer_phone: str,
        service: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Check availability and book an appointment if the slot is free.
        
        This combines conflict checking and appointment creation for convenience.
        
        Returns:
            {
                "success": bool,
                "appointment": Appointment or None,
                "calendar_event": dict or None,
                "conflicts": list,
                "message": str
            }
        """
        # Check local database conflicts first (all appointments)
        db_conflicts = self.check_db_conflicts(business_id, start_time, end_time, db)
        
        if db_conflicts:
            return {
                "success": False,
                "appointment": None,
                "calendar_event": None,
                "conflicts": db_conflicts,
                "message": "This time slot conflicts with an existing appointment."
            }
        
        # Check external calendar conflicts if integration exists
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.status == "active"
        ).first()
        
        calendar_conflicts = []
        if integration:
            try:
                availability = await self.check_availability(integration, start_time, end_time, db)
                if not availability.get("available"):
                    calendar_conflicts = availability.get("conflicts", [])
                    return {
                        "success": False,
                        "appointment": None,
                        "calendar_event": None,
                        "conflicts": calendar_conflicts,
                        "message": "This time slot is not available in the external calendar."
                    }
            except Exception as e:
                print(f"[Calendar Service] Could not check external calendar availability: {e}")
                # Continue anyway if external calendar check fails - local DB check passed
        
        # Create the appointment with source="internal"
        appointment = Appointment(
            business_id=business_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            appointment_time=start_time,
            service_type=service,
            status="scheduled",
            source="internal" # Mark as internal appointment
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        # Sync to external calendar (only if internal appointment)
        calendar_event = None
        if integration and appointment.source == "internal":
            try:
                calendar_event = await self.sync_appointment_to_calendar(appointment.id, db)
            except Exception as e:
                print(f"[Calendar Service] Could not sync to external calendar: {e}")
        
        return {
            "success": True,
            "appointment": appointment,
            "calendar_event": calendar_event,
            "conflicts": [],
            "message": f"Appointment scheduled for {start_time.strftime('%B %d at %I:%M %p')}"
        }
    
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
