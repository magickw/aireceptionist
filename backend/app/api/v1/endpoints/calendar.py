"""
Calendar API Endpoints

Provides endpoints for:
- OAuth flow initiation (Google, Microsoft)
- Calendar integration management
- Event creation and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.api import deps
from app.services.calendar_service import calendar_service
from app.models.models import Appointment as DBAppointment, Business # Import Appointment model
from app.schemas.appointment import AppointmentCreate # Import AppointmentCreate schema

router = APIRouter()


# Request/Response models
class CalendarEventCreate(BaseModel):
    summary: str
    description: str
    start_time: datetime
    end_time: datetime
    attendees: Optional[List[str]] = None


class CalendarEventResponse(BaseModel):
    id: str
    summary: str
    description: str
    start: str
    end: str
    attendees: List[str] = []


class ImportEventsResponse(BaseModel):
    message: str
    imported_count: int
    failed_count: int
    failed_events: List[dict]


@router.get("/connect/google")
async def connect_google(
    business_id: int = Depends(deps.get_current_business_id)
):
    """Get Google OAuth URL for calendar connection"""
    auth_url = calendar_service.get_google_auth_url(business_id)
    return {"auth_url": auth_url}


@router.get("/connect/microsoft")
async def connect_microsoft(
    business_id: int = Depends(deps.get_current_business_id)
):
    """Get Microsoft OAuth URL for calendar connection"""
    auth_url = calendar_service.get_microsoft_auth_url(business_id)
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Handle Google OAuth callback"""
    try:
        integration = await calendar_service.exchange_google_code(code, business_id, db)
        return {
            "success": True,
            "message": "Google Calendar connected successfully",
            "integration_id": integration.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_integrations(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """List all calendar integrations"""
    integrations = calendar_service.list_integrations(business_id, db)
    
    return {
        "integrations": [
            {
                "id": i.id,
                "provider": i.provider,
                "calendar_id": i.calendar_id,
                "status": i.status,
                "last_sync_at": i.last_sync_at.isoformat() if i.last_sync_at else None,
                "created_at": i.created_at.isoformat()
            }
            for i in integrations
        ]
    }


@router.get("/{integration_id}")
async def get_integration(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Get a specific calendar integration"""
    integration = calendar_service.get_integration(integration_id, business_id, db)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {
        "integration": {
            "id": integration.id,
            "provider": integration.provider,
            "calendar_id": integration.calendar_id,
            "status": integration.status,
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
            "token_expires_at": integration.token_expires_at.isoformat() if integration.token_expires_at else None
        }
    }


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Delete a calendar integration"""
    success = calendar_service.delete_integration(integration_id, business_id, db)
    
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {"success": True, "message": "Calendar integration deleted"}


@router.post("/{integration_id}/events")
async def create_event(
    integration_id: int,
    event_data: CalendarEventCreate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Create a calendar event"""
    integration = calendar_service.get_integration(integration_id, business_id, db)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        result = await calendar_service.create_calendar_event(
            integration=integration,
            summary=event_data.summary,
            description=event_data.description,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            attendees=event_data.attendees,
            db=db
        )
        
        return {
            "success": True,
            "event": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/events")
async def get_events(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get calendar events"""
    integration = calendar_service.get_integration(integration_id, business_id, db)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Default to next 30 days
    if not start_date:
        start_date = datetime.utcnow()
    if not end_date:
        end_date = start_date + timedelta(days=30)
    
    try:
        events = await calendar_service.get_calendar_events(
            integration=integration,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return {
            "events": [
                {
                    "id": e.get("id"),
                    "summary": e.get("summary"),
                    "description": e.get("description"),
                    "start": e.get("start", {}).get("dateTime"),
                    "end": e.get("end", {}).get("dateTime"),
                    "attendees": [a.get("email") for a in e.get("attendees", []) if a.get("email")]
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-events", response_model=ImportEventsResponse)
async def import_external_events(
    integration_id: int = Query(..., description="ID of the external calendar integration to import from"),
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for events to import (YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[datetime] = Query(None, description="End date for events to import (YYYY-MM-DDTHH:MM:SS)"),
) -> Any:
    """
    Import events from an external calendar integration into the built-in appointments.
    """
    integration = calendar_service.get_integration(integration_id, business_id, db)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Default to next 30 days if no date range is provided
    if not start_date:
        start_date = datetime.utcnow()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    try:
        external_events = await calendar_service.get_calendar_events(
            integration=integration,
            start_date=start_date,
            end_date=end_date,
            db=db
        )

        imported_count = 0
        failed_count = 0
        failed_events = []

        for event in external_events:
            try:
                # Basic check for existing appointment to avoid duplicates
                # This could be more sophisticated (e.g., check event ID from external source)
                existing_appointment = db.query(DBAppointment).filter(
                    DBAppointment.business_id == business_id,
                    DBAppointment.appointment_time == datetime.fromisoformat(event.get("start", {}).get("dateTime").replace("Z", "+00:00")),
                    DBAppointment.customer_name == event.get("summary"),
                    DBAppointment.source == integration.provider # Check if already imported from this source
                ).first()

                if existing_appointment:
                    # Skip if already imported
                    continue

                customer_name = event.get("summary", "External Event")
                # Attempt to extract phone from description or attendees
                customer_phone = "N/A"
                if event.get("description"):
                    # Simple regex to find a phone number
                    import re
                    phone_match = re.search(r'(\+?\d{1,2}\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', event.get("description"))
                    if phone_match:
                        customer_phone = phone_match.group(0)

                # Ensure start/end times are valid
                start_time_str = event.get("start", {}).get("dateTime")
                if not start_time_str:
                    raise ValueError("Event start time missing")
                
                appointment_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

                appointment_in = AppointmentCreate(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    appointment_time=appointment_time,
                    service_type=event.get("description", "")[:100], # Truncate description for service_type
                    status="scheduled",
                    business_id=business_id,
                    source=integration.provider # Mark source as the external provider
                )

                db_obj = DBAppointment(
                    **appointment_in.dict(),
                    source=integration.provider,
                )
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
                imported_count += 1
            except Exception as e:
                db.rollback()
                failed_count += 1
                failed_events.append({"event": event, "error": str(e)})

        return ImportEventsResponse(
            message=f"Successfully imported {imported_count} events.",
            imported_count=imported_count,
            failed_count=failed_count,
            failed_events=failed_events
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import events: {str(e)}")
