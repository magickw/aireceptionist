"""
Voice Greeting Service
Manages custom voice greetings for businesses
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import os


class VoiceGreetingService:
    """Service for managing custom voice greetings"""
    
    def __init__(self):
        self.enabled = True
        self.greeting_types = [
            "welcome",
            "after_hours",
            "voicemail",
            "hold",
            "transfer",
            "goodbye"
        ]
    
    def create_greeting(
        self,
        db: Session,
        business_id: int,
        name: str,
        greeting_type: str,
        text: str,
        language: str = "en"
    ) -> Dict:
        """Create a new voice greeting"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise ValueError("Business not found")
        
        # Store greeting metadata (in production, would store audio file)
        greeting_data = {
            "name": name,
            "greeting_type": greeting_type,
            "text": text,
            "language": language,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": False
        }
        
        # Update business settings
        if not business.settings:
            business.settings = {}
        
        greetings = business.settings.get("voice_greetings", {})
        greetings[greeting_type] = greeting_data
        business.settings["voice_greetings"] = greetings
        db.commit()
        
        return greeting_data
    
    def update_greeting(
        self,
        db: Session,
        business_id: int,
        greeting_type: str,
        is_active: bool = None,
        text: str = None
    ) -> Dict:
        """Update a voice greeting"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise ValueError("Business not found")
        
        greetings = business.settings.get("voice_greetings", {})
        
        if greeting_type not in greetings:
            raise ValueError(f"Greeting type {greeting_type} not found")
        
        if is_active is not None:
            # Deactivate other greetings of same type
            for gtype, greeting in greetings.items():
                if gtype != greeting_type and isinstance(greeting, dict):
                    greeting["is_active"] = False
            
            greetings[greeting_type]["is_active"] = is_active
        
        if text is not None:
            greetings[greeting_type]["text"] = text
            greetings[greeting_type]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        business.settings["voice_greetings"] = greetings
        db.commit()
        
        return greetings[greeting_type]
    
    def get_greetings(
        self,
        db: Session,
        business_id: int
    ) -> List[Dict]:
        """Get all greetings for a business"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return []
        
        greetings = business.settings.get("voice_greetings", {})
        
        return [
            {"type": gtype, **greeting} 
            for gtype, greeting in greetings.items()
            if isinstance(greeting, dict)
        ]
    
    def get_active_greeting(
        self,
        db: Session,
        business_id: int,
        greeting_type: str
    ) -> Optional[Dict]:
        """Get active greeting of specific type"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return None
        
        greetings = business.settings.get("voice_greetings", {})
        greeting = greetings.get(greeting_type, {})
        
        if isinstance(greeting, dict) and greeting.get("is_active"):
            return greeting
        
        return None
    
    def delete_greeting(
        self,
        db: Session,
        business_id: int,
        greeting_type: str
    ) -> bool:
        """Delete a voice greeting"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return False
        
        greetings = business.settings.get("voice_greetings", {})
        
        if greeting_type in greetings:
            del greetings[greeting_type]
            business.settings["voice_greetings"] = greetings
            db.commit()
            return True
        
        return False
    
    def get_available_types(self) -> List[str]:
        """Get available greeting types"""
        return self.greeting_types
    
    def generate_text_preview(
        self,
        business_name: str,
        greeting_type: str
    ) -> str:
        """Generate preview text for a greeting type"""
        templates = {
            "welcome": f"Thank you for calling {business_name}. Please hold while we connect you.",
            "after_hours": f"Thank you for calling {business_name}. Our offices are now closed.",
            "voicemail": f"All agents are currently busy. Please leave a message.",
            "hold": f"Please hold on. An agent will be with you shortly.",
            "transfer": f"Please hold while we transfer your call.",
            "goodbye": f"Thank you for calling {business_name}. Goodbye!"
        }
        return templates.get(greeting_type, "")


voice_greeting_service = VoiceGreetingService()
