"""
Chatbot Service - Web Chat Integration
Provides chatbot capabilities for web widget integration
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import os


class ChatbotService:
    """Service for web chatbot integration"""
    
    def __init__(self):
        self.enabled = True
    
    def create_chat_session(
        self,
        db: Session,
        business_id: int,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict:
        """Create a new chat session"""
        from app.models.models import CallSession
        
        session = CallSession(
            business_id=business_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            channel="chat",
            status="active",
            start_time=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "session_id": session.id,
            "created_at": session.start_time.isoformat()
        }
    
    def process_message(
        self,
        db: Session,
        session_id: int,
        message: str,
        business_id: int
    ) -> Dict:
        """Process a chat message and return AI response"""
        import asyncio
        from app.services.nova_reasoning import nova_reasoning
        
        # Get conversation context
        context = self._get_conversation_context(db, session_id)
        
        # Build business context (simplified for chat)
        business_context = {"business_id": business_id}
        
        # Process with Nova (async method needs to be run in event loop)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(
            nova_reasoning.reason(
                conversation=message,
                business_context=business_context,
                customer_context={"name": "Chat User"},
                db=db
            )
        )
        
        # Store the message exchange
        self._store_message(db, session_id, "customer", message)
        self._store_message(db, session_id, "agent", response.get("suggested_response", ""))
        
        return {
            "response": response.get("suggested_response", ""),
            "intent": response.get("intent"),
            "entities": response.get("entities", {}),
            "suggestions": []
        }
    
    def _get_conversation_context(self, db: Session, session_id: int) -> List[Dict]:
        """Get conversation history for context"""
        from app.models.models import CallSession
        
        # This would be a separate ChatMessage model in production
        # For now, return empty context
        return []
    
    def _store_message(
        self,
        db: Session,
        session_id: int,
        sender: str,
        content: str
    ):
        """Store a message in the conversation"""
        # Would create ChatMessage model in production
        pass
    
    def end_chat_session(
        self,
        db: Session,
        session_id: int
    ) -> Dict:
        """End a chat session"""
        from app.models.models import CallSession
        
        session = db.query(CallSession).filter(CallSession.id == session_id).first()
        if session:
            session.status = "completed"
            session.end_time = datetime.utcnow()
            db.commit()
        
        return {"success": True, "session_id": session_id}
    
    def get_chat_history(
        self,
        db: Session,
        business_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get chat session history"""
        from app.models.models import CallSession
        
        sessions = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.channel == "chat"
        ).order_by(CallSession.start_time.desc()).limit(limit).all()
        
        return [{
            "id": s.id,
            "customer_name": s.customer_name,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "status": s.status
        } for s in sessions]


chatbot_service = ChatbotService()
