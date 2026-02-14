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
    business_id: int = Query(...),
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
                    "attendees": [a.get("email") for a in e.get("attendees", [])]
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
