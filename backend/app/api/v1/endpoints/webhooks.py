"""
Webhook API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.api import deps
from app.services.webhook_service import webhook_service


router = APIRouter()


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    status: Optional[str] = None


@router.get("")
async def list_webhooks(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    status: Optional[str] = None
):
    webhooks = webhook_service.list_webhooks(business_id, db, status)
    return {"webhooks": [{"id": w.id, "name": w.name, "url": w.url, "events": w.events, "status": w.status} for w in webhooks]}


@router.get("/events")
async def get_available_events():
    return {"events": webhook_service.get_available_events()}


@router.post("")
async def create_webhook(
    webhook_data: WebhookCreate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    try:
        webhook = webhook_service.create_webhook(business_id=business_id, name=webhook_data.name, url=webhook_data.url, events=webhook_data.events, db=db, secret=webhook_data.secret)
        return {"success": True, "webhook_id": webhook.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: int, business_id: int = Depends(deps.get_current_business_id), db: Session = Depends(deps.get_db)):
    success = webhook_service.delete_webhook(webhook_id, business_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"success": True}
