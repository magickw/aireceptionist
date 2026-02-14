"""
Email API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api import deps
from app.services.email_service import email_service


router = APIRouter()


class EmailSendRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    html: bool = False


class CallNotificationRequest(BaseModel):
    to_email: str
    customer_name: str
    phone_number: str
    call_summary: str


class AppointmentReminderRequest(BaseModel):
    to_email: str
    customer_name: str
    appointment_time: str
    business_name: str


@router.get("/status")
async def get_email_status():
    return {
        "enabled": email_service.enabled,
        "provider": "SMTP" if email_service.enabled else "Not configured"
    }


@router.post("/send")
async def send_email(email_data: EmailSendRequest):
    result = email_service.send_email(
        to_email=email_data.to_email,
        subject=email_data.subject,
        body=email_data.body,
        html=email_data.html
    )
    return result


@router.post("/call-notification")
async def send_call_notification(notification: CallNotificationRequest):
    result = email_service.send_call_notification(
        to_email=notification.to_email,
        customer_name=notification.customer_name,
        phone_number=notification.phone_number,
        call_summary=notification.call_summary
    )
    return result


@router.post("/appointment-reminder")
async def send_appointment_reminder(reminder: AppointmentReminderRequest):
    result = email_service.send_appointment_reminder(
        to_email=reminder.to_email,
        customer_name=reminder.customer_name,
        appointment_time=reminder.appointment_time,
        business_name=reminder.business_name
    )
    return result
