"""
Email Service - Email Notifications
Uses SMTP for sending email notifications
"""

from typing import Optional, List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.enabled = bool(os.getenv("SMTP_HOST"))
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM", self.smtp_user)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict:
        """Send an email"""
        if not self.enabled:
            return {"success": False, "error": "SMTP not configured"}
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return {"success": True, "message": "Email sent"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_call_notification(
        self,
        to_email: str,
        customer_name: str,
        phone_number: str,
        call_summary: str
    ) -> Dict:
        """Send call notification email"""
        subject = f"New Call from {customer_name}"
        body = f"""
New call received

Customer: {customer_name}
Phone: {phone_number}

Summary:
{call_summary}

---
AI Receptionist Pro
"""
        return self.send_email(to_email, subject, body)
    
    def send_appointment_reminder(
        self,
        to_email: str,
        customer_name: str,
        appointment_time: str,
        business_name: str
    ) -> Dict:
        """Send appointment reminder email"""
        subject = f"Appointment Reminder - {business_name}"
        body = f"""
Hi {customer_name},

This is a reminder about your upcoming appointment:

Time: {appointment_time}
Business: {business_name}

Please let us know if you need to reschedule.

---
{business_name}
"""
        return self.send_email(to_email, subject, body)
    
    def send_voicemail_notification(
        self,
        to_email: str,
        customer_name: str,
        phone_number: str,
        voicemail_transcription: str
    ) -> Dict:
        """Send voicemail notification email"""
        subject = f"New Voicemail from {customer_name}"
        body = f"""
New voicemail received

Customer: {customer_name}
Phone: {phone_number}

Transcription:
{voicemail_transcription}

---
AI Receptionist Pro
"""
        return self.send_email(to_email, subject, body)


email_service = EmailService()
