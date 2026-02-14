"""
Voice Greetings API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api import deps
from app.services.voice_greeting_service import voice_greeting_service


router = APIRouter()


class GreetingCreate(BaseModel):
    name: str
    greeting_type: str
    text: str
    language: str = "en"


class GreetingUpdate(BaseModel):
    is_active: Optional[bool] = None
    text: Optional[str] = None


@router.get("/types")
async def get_greeting_types():
    types = voice_greeting_service.get_available_types()
    return {"types": types}


@router.get("")
async def list_greetings(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    greetings = voice_greeting_service.get_greetings(db, business_id)
    return {"greetings": greetings}


@router.post("")
async def create_greeting(
    greeting_data: GreetingCreate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    try:
        greeting = voice_greeting_service.create_greeting(
            db=db,
            business_id=business_id,
            name=greeting_data.name,
            greeting_type=greeting_data.greeting_type,
            text=greeting_data.text,
            language=greeting_data.language
        )
        return {"success": True, "greeting": greeting}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@router.put("/{greeting_type}")
async def update_greeting(
    greeting_type: str,
    greeting_data: GreetingUpdate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    try:
        greeting = voice_greeting_service.update_greeting(
            db=db,
            business_id=business_id,
            greeting_type=greeting_type,
            is_active=greeting_data.is_active,
            text=greeting_data.text
        )
        return {"success": True, "greeting": greeting}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@router.delete("/{greeting_type}")
async def delete_greeting(
    greeting_type: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    success = voice_greeting_service.delete_greeting(db, business_id, greeting_type)
    return {"success": success}


@router.get("/preview/{greeting_type}")
async def get_greeting_preview(
    greeting_type: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    from app.models.models import Business
    business = db.query(Business).filter(Business.id == business_id).first()
    business_name = business.name if business else "Your Business"
    
    preview = voice_greeting_service.generate_text_preview(business_name, greeting_type)
    return {"preview": preview}
