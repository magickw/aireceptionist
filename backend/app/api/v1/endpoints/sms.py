"""
SMS Notification API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.api import deps
from app.services.sms_service import sms_service


router = APIRouter()


class SMSTemplateCreate(BaseModel):
    name: str
    event_type: str
    content: str
    is_active: bool = True


class SMSSendRequest(BaseModel):
    to_number: str
    message: str
    media_url: Optional[str] = None


@router.get("/templates")
async def list_templates(business_id: int = Depends(deps.get_current_business_id), db: Session = Depends(deps.get_db)):
    templates = sms_service.list_templates(business_id, db)
    return {"templates": [{"id": t.id, "name": t.name, "event_type": t.event_type, "content": t.content} for t in templates]}


@router.post("/templates")
async def create_template(template_data: SMSTemplateCreate, business_id: int = Depends(deps.get_current_business_id), db: Session = Depends(deps.get_db)):
    try:
        template = sms_service.create_template(business_id=business_id, name=template_data.name, event_type=template_data.event_type, content=template_data.content, db=db)
        return {"success": True, "template_id": template.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send")
async def send_sms(sms_data: SMSSendRequest, business_id: int = Depends(deps.get_current_business_id)):
    result = await sms_service.send_sms(to_number=sms_data.to_number, message=sms_data.message, media_url=sms_data.media_url)
    return result


@router.get("/status")
async def get_sms_status():
    return {"enabled": sms_service.enabled, "provider": "Twilio" if sms_service.enabled else "Not configured"}
