from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from app.models.models import Appointment as DBAppointment
from app.models.models import Business
from app.api.deps import get_current_active_user # Corrected import path
from app.services.calendar_service import calendar_service
from datetime import date, datetime

router = APIRouter()

@router.post("/appointments", response_model=Appointment, status_code=201)
def create_builtin_appointment(
    *,
    db: Session = Depends(deps.get_db),
    appointment_in: AppointmentCreate,
    current_user: Any = Depends(get_current_active_user)
) -> Any:
    """
    Create a new built-in appointment.
    """
    # Ensure the business exists and belongs to the current user
    business = db.query(Business).filter(
        Business.id == appointment_in.business_id,
        Business.user_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found or not owned by user")

    db_obj = DBAppointment(
        **appointment_in.dict(),
        source="internal", # Ensure source is internal for built-in appointments
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/appointments", response_model=List[Appointment])
def read_builtin_appointments(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(get_current_active_user),
    business_id: int = Query(..., description="ID of the business to retrieve appointments for"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve built-in appointments.
    """
    query = db.query(DBAppointment).filter(DBAppointment.source == "internal")

    # Ensure the business exists and belongs to the current user
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found or not owned by user")
    query = query.filter(DBAppointment.business_id == business_id)

    appointments = query.offset(skip).limit(limit).all()
    return appointments

@router.put("/appointments/{appointment_id}", response_model=Appointment)
def update_builtin_appointment(
    *,
    db: Session = Depends(deps.get_db),
    appointment_id: int,
    appointment_in: AppointmentUpdate,
    current_user: Any = Depends(get_current_active_user)
) -> Any:
    """
    Update an existing built-in appointment.
    """
    appointment = db.query(DBAppointment).filter(
        DBAppointment.id == appointment_id,
        DBAppointment.source == "internal"
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Built-in appointment not found")

    # Ensure the appointment's business belongs to the current user
    business = db.query(Business).filter(
        Business.id == appointment.business_id,
        Business.user_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

    update_data = appointment_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.delete("/appointments/{appointment_id}", status_code=204)
def delete_builtin_appointment(
    *,
    db: Session = Depends(deps.get_db),
    appointment_id: int,
    current_user: Any = Depends(get_current_active_user)
) -> Any:
    """
    Delete a built-in appointment.
    """
    appointment = db.query(DBAppointment).filter(
        DBAppointment.id == appointment_id,
        DBAppointment.source == "internal"
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Built-in appointment not found")

    # Ensure the appointment's business belongs to the current user
    business = db.query(Business).filter(
        Business.id == appointment.business_id,
        Business.user_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(status_code=403, detail="Not authorized to delete this appointment")

    db.delete(appointment)
    db.commit()
    return None


@router.get("/availability", response_model=List[dict])
async def get_availability(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(get_current_active_user),
    business_id: int = Query(..., description="ID of the business to check availability for"),
    date_str: str = Query(..., description="Date for availability check (YYYY-MM-DD)"),
    duration_minutes: int = Query(60, description="Duration of the desired appointment slot in minutes"),
) -> Any:
    """
    Retrieve available time slots for a business on a specific date,
    considering operating hours and existing appointments.
    """
    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # Ensure the business exists and belongs to the current user
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found or not owned by user")

    available_slots = await calendar_service.get_business_availability(
        business_id=business_id,
        date=check_date,
        duration_minutes=duration_minutes,
        db=db
    )
    return available_slots