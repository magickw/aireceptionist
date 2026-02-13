from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.models import Appointment, User, Business
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, Appointment as AppointmentSchema

router = APIRouter()

@router.get("/business/{business_id}", response_model=List[AppointmentSchema])
def read_appointments(
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve appointments for a business.
    """
    if current_user.role != "admin":
         business = db.query(Business).filter(Business.id == business_id).first()
         if not business or business.user_id != current_user.id:
             raise HTTPException(status_code=400, detail="Not enough permissions")

    appointments = db.query(Appointment).filter(Appointment.business_id == business_id).all()
    return appointments

@router.post("/", response_model=AppointmentSchema)
def create_appointment(
    *,
    db: Session = Depends(deps.get_db),
    appointment_in: AppointmentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new appointment.
    """
    if current_user.role != "admin":
         business = db.query(Business).filter(Business.id == appointment_in.business_id).first()
         if not business or business.user_id != current_user.id:
             raise HTTPException(status_code=400, detail="Not enough permissions")

    appointment = Appointment(**appointment_in.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.put("/{id}", response_model=AppointmentSchema)
def update_appointment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    appointment_in: AppointmentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an appointment.
    """
    appointment = db.query(Appointment).filter(Appointment.id == id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.role != "admin":
         business = db.query(Business).filter(Business.id == appointment.business_id).first()
         if not business or business.user_id != current_user.id:
             raise HTTPException(status_code=400, detail="Not enough permissions")

    for field, value in appointment_in.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
