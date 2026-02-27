from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.models import Business, Appointment, Order, Customer

router = APIRouter()

@router.get("/business/{business_id}/profile")
async def get_portal_business_profile(
    business_id: int,
    db: Session = Depends(deps.get_db)
):
    """Publicly accessible business profile for the portal."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    return {
        "name": business.name,
        "address": business.address,
        "phone": business.phone,
        "website": business.website,
        "type": business.type,
        "operating_hours": business.operating_hours,
        "welcome_message": business.settings.get("welcome_message") if business.settings else ""
    }

@router.post("/verify")
async def portal_verify_customer(
    business_id: int = Body(...),
    phone: str = Body(...),
    db: Session = Depends(deps.get_db)
):
    """
    Verify customer via phone and return a temporary portal token.
    In production, this would send an SMS OTP.
    """
    customer = db.query(Customer).filter(
        Customer.business_id == business_id,
        Customer.phone == phone
    ).first()
    
    if not customer:
        # Create a basic customer record if they don't exist yet (first time portal user)
        customer = Customer(
            business_id=business_id,
            phone=phone,
            name="New Customer"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    # For prototype, we return a simple successful verification
    return {
        "success": True,
        "customer_id": customer.id,
        "token": f"portal_token_{customer.id}_{datetime.now().timestamp()}"
    }

@router.get("/appointments")
async def get_portal_appointments(
    phone: str = Query(...),
    business_id: int = Query(...),
    db: Session = Depends(deps.get_db)
):
    """Get appointments for a specific customer in the portal."""
    appts = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.customer_phone == phone
    ).order_by(Appointment.appointment_time.desc()).all()
    
    return appts

@router.get("/orders")
async def get_portal_orders(
    phone: str = Query(...),
    business_id: int = Query(...),
    db: Session = Depends(deps.get_db)
):
    """Get orders for a specific customer in the portal."""
    orders = db.query(Order).filter(
        Order.business_id == business_id,
        Order.customer_phone == phone
    ).order_by(Order.created_at.desc()).all()
    
    return orders
