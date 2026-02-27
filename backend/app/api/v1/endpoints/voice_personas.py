from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import User
from app.services.voice_cloning_service import voice_cloning_service

router = APIRouter()

@router.get("/available")
async def list_personas():
    """List all available predefined voice personas."""
    return {"personas": voice_cloning_service.list_available_personas()}

@router.get("/current")
async def get_current_persona(
    db: Session = Depends(deps.get_db),
    business_id: int = Depends(deps.get_current_business_id)
):
    """Get the current voice configuration for the business."""
    persona = await voice_cloning_service.get_business_voice(db, business_id)
    return {"persona": persona}

@router.post("/set")
async def set_persona(
    db: Session = Depends(deps.get_db),
    business_id: int = Depends(deps.get_current_business_id),
    persona_name: str = Body(..., embed=True),
    customizations: Dict = Body({}, embed=True)
):
    """Set the voice persona for the business."""
    result = await voice_cloning_service.create_custom_voice(
        db=db,
        business_id=business_id,
        voice_name=persona_name,
        base_persona=persona_name,
        customizations=customizations
    )
    return result

@router.post("/preview")
async def preview_voice(
    text: str = Body(..., embed=True),
    persona_name: str = Body("professional", embed=True)
):
    """Generate a sample audio for a persona."""
    import base64
    result = await voice_cloning_service.synthesize_speech(text, persona_name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Return as base64 for easy frontend playback
    audio_b64 = base64.b64encode(result["audio_data"]).decode('utf-8')
    return {
        "audio_base64": audio_b64,
        "content_type": result["content_type"]
    }
