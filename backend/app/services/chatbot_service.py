"""
Chatbot Service - Web Chat Integration with Rich Business Context
Provides enhanced chatbot capabilities for web widget integration
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import json
import os


class ChatbotService:
    """Enhanced service for web chatbot integration with rich context"""
    
    def __init__(self):
        self.enabled = True
        self._session_states = {}  # In-memory session state (should use Redis in production)
    
    async def create_chat_session(
        self,
        db: Session,
        business_id: int,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict:
        """Create a new chat session with order state initialization"""
        from app.models.models import CallSession
        from app.services.conversation_state import OrderState, ConversationMemory
        
        session = CallSession(
            business_id=business_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            status="active",
            started_at=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Initialize order state for this session
        self._session_states[session.id] = {
            "order_state": OrderState(),
            "conversation_memory": ConversationMemory(),
            "collected_fields": {},
            "price_mentioned": False
        }
        
        return {
            "session_id": session.id,
            "created_at": session.started_at.isoformat()
        }
    
    async def process_message(
        self,
        db: Session,
        session_id: str,
        message: str,
        business_id: int
    ) -> Dict:
        """Process a chat message with rich business context and order state"""
        from app.services.nova_reasoning import nova_reasoning
        from app.services.business_templates import BusinessTypeTemplate
        from app.services.knowledge_base import knowledge_base_service
        
        # Get or initialize session state
        if session_id not in self._session_states:
            self._session_states[session_id] = {
                "order_state": OrderState(),
                "conversation_memory": ConversationMemory(),
                "collected_fields": {},
                "price_mentioned": False
            }
        
        session_state = self._session_states[session_id]
        order_state = session_state["order_state"]
        conversation_memory = session_state["conversation_memory"]
        
        # Get rich business context (same as voice endpoint)
        business_context = await self._get_business_context(db, business_id)
        
        # Get conversation history
        conversation_history = self._get_conversation_history(db, session_id)
        
        # Build customer context
        customer_context = {
            "name": session_state.get("customer_name"),
            "phone": session_state.get("customer_phone"),
            "history": conversation_history,
            "collected_fields": session_state["collected_fields"]
        }
        
        # Get knowledge base context
        knowledge_context = await knowledge_base_service.get_relevant_context(
            query=message,
            business_id=business_id,
            db=db,
            max_chars=1500
        )
        
        # Process with Nova Reasoning
        response = await nova_reasoning.reason(
            conversation=message,
            business_context=business_context,
            customer_context=customer_context,
            db=db,
            knowledge_context=knowledge_context
        )
        
        # Update conversation memory
        conversation_memory.update(response)
        
        # Update order state if applicable
        if response.get("selected_action") in ["PLACE_ORDER", "CONFIRM_ORDER"]:
            order_update = conversation_memory.update_order(
                response.get("selected_action"),
                response.get("entities", {}),
                business_context.get("menu", [])
            )
            session_state["order_state"] = order_update
        
        # Store the message exchange
        await self._store_message(db, session_id, "customer", message, response)
        await self._store_message(db, session_id, "ai", response.get("suggested_response", ""), response)
        
        # Build response with order state info
        result = {
            "response": response.get("suggested_response", ""),
            "intent": response.get("intent"),
            "entities": response.get("entities", {}),
            "action": response.get("selected_action"),
            "order_state": order_state.get_summary() if order_state else None,
            "suggestions": response.get("suggestions", [])
        }
        
        # Add order total if available
        if order_state and order_state.get("status") in ["building", "pending_confirmation"]:
            result["order_total"] = order_state.get("total_amount")
        
        return result
    
    async def _get_business_context(
        self,
        db: Session,
        business_id: int
    ) -> Dict[str, Any]:
        """
        Get rich business context with all relevant information.
        Matches the implementation in voice endpoint.
        """
        from app.models.models import Business, MenuItem
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {}
        
        # Get services from business settings
        services = business.settings.get("services", []) if business.settings else []
        
        # Get menu items
        menu_items = db.query(MenuItem).filter(
            MenuItem.business_id == business_id,
            MenuItem.is_active == True
        ).all()
        
        menu = [
            {
                "name": item.name,
                "price": float(item.price) if item.price else 0,
                "description": item.description,
                "category": item.category,
                "unit": item.unit,
                "dietary_info": item.dietary_info
            }
            for item in menu_items
        ]
        
        return {
            "business_id": business_id,
            "name": business.name,
            "type": business.type or "general",
            "address": business.address,
            "phone": business.phone,
            "website": business.website,
            "description": business.description,
            "services": services,
            "operating_hours": business.settings.get("operating_hours") if business.settings else None,
            "available_slots": business.settings.get("available_slots") if business.settings else None,
            "menu": menu
        }
    
    def _get_conversation_history(self, db: Session, session_id: str) -> List[Dict]:
        """Get conversation history for context"""
        from app.models.models import ConversationMessage
        
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.call_session_id == session_id
        ).order_by(ConversationMessage.timestamp).limit(20).all()
        
        return [
            {
                "sender": msg.sender,
                "content": msg.content,
                "intent": msg.intent,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            }
            for msg in messages
        ]
    
    async def _store_message(
        self,
        db: Session,
        session_id: str,
        sender: str,
        content: str,
        reasoning_result: Optional[Dict] = None
    ):
        """Store a message in the conversation"""
        from app.models.models import ConversationMessage
        
        message = ConversationMessage(
            call_session_id=session_id,
            sender=sender,
            content=content,
            intent=reasoning_result.get("intent") if reasoning_result else None,
            entities=reasoning_result.get("entities") if reasoning_result else None,
            confidence=reasoning_result.get("confidence") if reasoning_result else None
        )
        db.add(message)
        db.commit()
    
    async def end_chat_session(
        self,
        db: Session,
        session_id: str
    ) -> Dict:
        """End a chat session and save final state"""
        from app.models.models import CallSession
        
        session = db.query(CallSession).filter(CallSession.id == session_id).first()
        if session:
            session.status = "ended"
            session.ended_at = datetime.now(timezone.utc)
            
            # Calculate duration
            if session.started_at:
                duration = (session.ended_at - session.started_at).total_seconds()
                session.duration_seconds = int(duration)
            
            db.commit()
        
        # Clean up session state
        if session_id in self._session_states:
            del self._session_states[session_id]
        
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
            CallSession.business_id == business_id
        ).order_by(CallSession.started_at.desc()).limit(limit).all()
        
        return [{
            "id": s.id,
            "customer_name": s.customer_name,
            "customer_phone": s.customer_phone,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "duration_seconds": s.duration_seconds,
            "sentiment": s.sentiment
        } for s in sessions]
    
    def get_session_messages(
        self,
        db: Session,
        session_id: str
    ) -> List[Dict]:
        """Get all messages for a specific session"""
        from app.models.models import ConversationMessage
        
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.call_session_id == session_id
        ).order_by(ConversationMessage.timestamp).all()
        
        return [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "message_type": msg.message_type,
                "intent": msg.intent,
                "entities": msg.entities,
                "confidence": float(msg.confidence) if msg.confidence else None,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            }
            for msg in messages
        ]


chatbot_service = ChatbotService()
