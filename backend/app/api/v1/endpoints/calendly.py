"""
Calendly API Endpoints

Provides endpoints for:
- OAuth flow initiation
- Webhook management
- Event type synchronization
- Booking retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

from app.api import deps
from app.services.calendly_service import calendly_service
from app.models.models import CalendarIntegration, Appointment as DBAppointment
from app.schemas.appointment import AppointmentCreate


router = APIRouter()


# Request/Response Models
class CalendlyWebhookCreate(BaseModel):
    url: str
    events: List[str]  # ["invitee.created", "invitee.canceled", etc.]


class CalendlyEventType(BaseModel):
    uri: str
    name: str
    description: Optional[str]
    duration_minutes: int
    active: bool


class CalendlyEvent(BaseModel):
    uri: str
    event_type: str
    start_time: datetime
    end_time: datetime
    invitee_name: str
    invitee_email: str
    status: str


@router.get("/connect/calendly")
async def connect_calendly(
    business_id: int = Depends(deps.get_current_business_id)
):
    """Get Calendly OAuth URL for calendar connection"""
    try:
        auth_url = calendly_service.get_calendly_auth_url(business_id)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback/calendly")
async def calendly_callback(
    code: str,
    state: str,
    db: Session = Depends(deps.get_db),
    business_id: int = Depends(deps.get_current_business_id)
):
    """
    Handle Calendly OAuth callback
    
    After user authorizes, Calendly redirects here with authorization code
    """
    try:
        # Verify state matches business_id (security check)
        if not state.startswith(f"{business_id}:"):
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange code for tokens
        integration = await calendly_service.exchange_calendly_code(
            code=code,
            business_id=business_id,
            db=db
        )
        
        return {
            "success": True,
            "integration": {
                "id": integration.id,
                "provider": integration.provider,
                "status": integration.status,
                "calendar_id": integration.calendar_id
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/event-types")
async def get_event_types(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Get all Calendly event types"""
    try:
        # Get integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.provider == "calendly"
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Calendly integration not found")
        
        if integration.status != "active":
            raise HTTPException(status_code=400, detail="Integration is not active")
        
        # Get event types from Calendly
        event_types = await calendly_service.get_event_types(integration, db)
        
        return {
            "success": True,
            "event_types": [
                {
                    "uri": et.get("uri"),
                    "name": et.get("name"),
                    "description": et.get("description"),
                    "duration_minutes": et.get("duration_minutes", 30),
                    "active": et.get("active", True)
                }
                for et in event_types
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/events")
async def get_scheduled_events(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Get scheduled events from Calendly"""
    try:
        # Get integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.provider == "calendly"
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Calendly integration not found")
        
        # Default to next 30 days
        if not start_time:
            start_time = datetime.now(timezone.utc)
        if not end_time:
            from datetime import timedelta
            end_time = start_time + timedelta(days=30)
        
        # Get events from Calendly
        events = await calendly_service.get_scheduled_events(
            integration, db, start_time, end_time
        )
        
        return {
            "success": True,
            "events": [
                {
                    "uri": e.get("uri"),
                    "event_type": e.get("event_type", {}).get("name"),
                    "start_time": e.get("start_time"),
                    "end_time": e.get("end_time"),
                    "invitee_name": e.get("name", ""),
                    "invitee_email": e.get("email", ""),
                    "status": e.get("status", "confirmed")
                }
                for e in events
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/webhooks")
async def create_webhook(
    integration_id: int,
    webhook_data: CalendlyWebhookCreate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Create Calendly webhook subscription
    
    This registers a webhook URL with Calendly to receive real-time events
    """
    try:
        # Get integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.provider == "calendly"
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Calendly integration not found")
        
        # Create webhook subscription
        result = await calendly_service.create_webhook_subscription(
            integration=integration,
            webhook_url=webhook_data.url,
            events=webhook_data.events,
            db=db
        )
        
        return {
            "success": True,
            "webhook": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{integration_id}/webhooks/{subscription_id}")
async def delete_webhook(
    integration_id: int,
    subscription_id: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Delete Calendly webhook subscription"""
    try:
        # Get integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.provider == "calendly"
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Calendly integration not found")
        
        # Delete webhook
        success = await calendly_service.delete_webhook_subscription(
            integration, subscription_id, db
        )
        
        return {
            "success": True,
            "message": "Webhook subscription deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/handler")
async def handle_webhook(
    request: Request,
    db: Session = Depends(deps.get_db),
    x_calendly_signature: Optional[str] = Header(None)
):
    """
    Handle incoming Calendly webhooks
    
    This endpoint receives real-time notifications from Calendly:
    - invitee.created: New booking
    - invitee.canceled: Cancellation
    - invitee_rescheduled: Rescheduled booking
    
    Calendly sends POST requests with event data and signature for verification
    """
    try:
        # Get raw payload
        payload = await request.json()
        
        # Process webhook event
        result = await calendly_service.handle_webhook_event(
            payload=payload,
            signature=x_calendly_signature or "",
            db=db
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        # Return 200 anyway to prevent Calendly from retrying
        print(f"Error processing Calendly webhook: {e}")
        return {
            "success": False,
            "error": str(e),
            "handled": True  # Acknowledge receipt
        }


@router.get("/{integration_id}/status")
async def get_integration_status(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """Get Calendly integration status and token expiration"""
    try:
        # Get integration
        integration = db.query(CalendarIntegration).filter(
            CalendarIntegration.id == integration_id,
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.provider == "calendly"
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Calendly integration not found")
        
        # Check token expiration
        token_expiring_soon = False
        if integration.token_expires_at:
            from datetime import timedelta
            token_expiring_soon = integration.token_expires_at < datetime.now(timezone.utc) + timedelta(minutes=30)
        
        return {
            "success": True,
            "integration": {
                "id": integration.id,
                "provider": integration.provider,
                "status": integration.status,
                "calendar_id": integration.calendar_id,
                "token_expires_at": integration.token_expires_at.isoformat() if integration.token_expires_at else None,
                "token_expiring_soon": token_expiring_soon,
                "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/import")
async def import_calendly_events(
    integration_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for events to import"),
    end_date: Optional[datetime] = Query(None, description="End date for events to import")
):
    """
    Import events from Calendly into built-in appointments.
    
    This fetches scheduled events from Calendly and creates internal appointments.
    """
    # Get integration
    integration = db.query(CalendarIntegration).filter(
        CalendarIntegration.id == integration_id,
        CalendarIntegration.business_id == business_id,
        CalendarIntegration.provider == "calendly"
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Calendly integration not found")
    
    if integration.status != "active":
        raise HTTPException(status_code=400, detail="Integration is not active")
    
    # Default to next 30 days if no date range provided
    if not start_date:
        start_date = datetime.now(timezone.utc)
    if not end_date:
        end_date = start_date + timedelta(days=30)
    
    try:
        # Get scheduled events from Calendly
        events = await calendly_service.get_scheduled_events(
            integration, db, start_date, end_date
        )
        
        imported_count = 0
        failed_count = 0
        failed_events = []
        
        for event in events:
            try:
                start_time_str = event.get("start_time")
                if not start_time_str:
                    continue
                
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                
                # Get invitee info
                invitee_name = event.get("name", "Unknown")
                invitee_email = event.get("email", "")
                event_type_name = event.get("event_type", {}).get("name", "Calendly Event")
                
                # Check for existing appointment to avoid duplicates
                existing = db.query(DBAppointment).filter(
                    DBAppointment.business_id == business_id,
                    DBAppointment.appointment_time == start_time,
                    DBAppointment.source == "calendly"
                ).first()
                
                if existing:
                    continue
                
                # Create appointment
                appointment = DBAppointment(
                    customer_name=invitee_name,
                    customer_phone="",  # Calendly doesn't provide phone directly
                    appointment_time=start_time,
                    service_type=event_type_name,
                    status="scheduled",
                    business_id=business_id,
                    source="calendly"
                )
                db.add(appointment)
                imported_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_events.append({"event": event.get("uri", "unknown"), "error": str(e)})
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully imported {imported_count} Calendly events",
            "imported_count": imported_count,
            "failed_count": failed_count,
            "failed_events": failed_events
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import Calendly events: {str(e)}")
