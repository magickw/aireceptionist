"""
Chatbot API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api import deps
from app.services.chatbot_service import chatbot_service


router = APIRouter()


class ChatMessageRequest(BaseModel):
    session_id: int
    message: str


class StartChatRequest(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


@router.post("/start")
async def start_chat(
    chat_data: StartChatRequest,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    result = chatbot_service.create_chat_session(
        db=db,
        business_id=business_id,
        customer_name=chat_data.customer_name,
        customer_email=chat_data.customer_email,
        customer_phone=chat_data.customer_phone
    )
    return result


@router.post("/message")
async def send_message(
    message_data: ChatMessageRequest,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    result = chatbot_service.process_message(
        db=db,
        session_id=message_data.session_id,
        message=message_data.message,
        business_id=business_id
    )
    return result


@router.post("/end/{session_id}")
async def end_chat(
    session_id: int,
    db: Session = Depends(deps.get_db)
):
    result = chatbot_service.end_chat_session(db=db, session_id=session_id)
    return result


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    history = chatbot_service.get_chat_history(db=db, business_id=business_id, limit=limit)
    return {"sessions": history}
