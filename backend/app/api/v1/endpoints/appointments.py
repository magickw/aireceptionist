from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.models import Appointment, User, Business
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, Appointment as AppointmentSchema
from app.services.audit_service import create_audit_log

router = APIRouter()

@router.get("/business/{business_id}", response_model=List[AppointmentSchema])
def read_appointments(
    business_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
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

    appointments = (
        db.query(Appointment)
        .filter(Appointment.business_id == business_id)
        .order_by(Appointment.appointment_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return appointments

@router.post("/", response_model=AppointmentSchema)
def create_appointment(
    *,
    request: Request,
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
    create_audit_log(
        db,
        user_id=current_user.id,
        business_id=appointment_in.business_id,
        operation="appointment.create",
        resource_type="appointment",
        new_values=appointment_in.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(appointment)
    return appointment

@router.put("/{id}", response_model=AppointmentSchema)
def update_appointment(
    *,
    request: Request,
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

    old_values = {
        "customer_name": appointment.customer_name,
        "customer_phone": appointment.customer_phone,
        "status": appointment.status,
    }
    for field, value in appointment_in.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    create_audit_log(
        db,
        user_id=current_user.id,
        business_id=appointment.business_id,
        operation="appointment.update",
        resource_type="appointment",
        resource_id=id,
        old_values=old_values,
        new_values=appointment_in.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
