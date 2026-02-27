"""
Voice Cloning Service
Custom brand voice and multiple agent personas using AWS Polly and advanced TTS
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import boto3
import os
from botocore.exceptions import ClientError

from app.core.config import settings


class VoicePersona:
    """Voice persona configuration"""
    
    # Predefined voice personas
    PERSONAS = {
        "professional": {
            "description": "Formal, business-like tone",
            "polly_voice_id": "Joanna",
            "engine": "neural",
            "language": "en-US",
            "style": "professional",
            "pitch": 0,
            "speed": 1.0
        },
        "friendly": {
            "description": "Warm, approachable tone",
            "polly_voice_id": "Salli",
            "engine": "neural",
            "language": "en-US",
            "style": "friendly",
            "pitch": 0,
            "speed": 1.0
        },
        "energetic": {
            "description": "Upbeat, enthusiastic tone",
            "polly_voice_id": "Ivy",
            "engine": "neural",
            "language": "en-US",
            "style": "energetic",
            "pitch": 2,
            "speed": 1.1
        },
        "calm": {
            "description": "Soothing, relaxed tone",
            "polly_voice_id": "Amy",
            "engine": "neural",
            "language": "en-GB",
            "style": "calm",
            "pitch": -2,
            "speed": 0.9
        },
        "authoritative": {
            "description": "Confident, commanding tone",
            "polly_voice_id": "Matthew",
            "engine": "neural",
            "language": "en-US",
            "style": "authoritative",
            "pitch": 0,
            "speed": 0.95
        },
        "casual": {
            "description": "Relaxed, conversational tone",
            "polly_voice_id": "Justin",
            "engine": "neural",
            "language": "en-US",
            "style": "casual",
            "pitch": 0,
            "speed": 1.0
        },
        "spanish_professional": {
            "description": "Professional Spanish voice",
            "polly_voice_id": "Lupe",
            "engine": "neural",
            "language": "es-US",
            "style": "professional",
            "pitch": 0,
            "speed": 1.0
        },
        "french_professional": {
            "description": "Professional French voice",
            "polly_voice_id": "Lea",
            "engine": "neural",
            "language": "fr-FR",
            "style": "professional",
            "pitch": 0,
            "speed": 1.0
        }
    }
    
    # Industry-specific persona recommendations
    INDUSTRY_PERSONAS = {
        "medical": "calm",
        "dental": "friendly",
        "restaurant": "energetic",
        "hotel": "professional",
        "law_firm": "authoritative",
        "salon": "friendly",
        "fitness": "energetic",
        "real_estate": "professional",
        "auto_repair": "casual",
        "hvac": "casual",
        "accounting": "professional",
        "education": "friendly"
    }


class VoiceCloningService:
    """Service for voice cloning and persona management"""
    
    def __init__(self):
        self.polly_client = boto3.client(
            'polly',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.voice_bucket = os.getenv('VOICE_ASSETS_BUCKET', 'receptium-voice-assets')
    
    def get_persona(self, persona_name: str) -> Optional[Dict]:
        """Get a predefined voice persona"""
        return VoicePersona.PERSONAS.get(persona_name)
    
    def get_recommended_persona(self, business_type: str) -> str:
        """Get recommended persona for a business type"""
        return VoicePersona.INDUSTRY_PERSONAS.get(business_type, "professional")
    
    def list_available_personas(self) -> List[Dict]:
        """List all available voice personas"""
        return [
            {
                "name": name,
                **config
            }
            for name, config in VoicePersona.PERSONAS.items()
        ]
    
    async def synthesize_speech(
        self,
        text: str,
        persona_name: str = "professional",
        output_format: str = "mp3",
        sample_rate: str = "22050"
    ) -> Dict:
        """Synthesize speech using a voice persona"""
        
        if not text or not text.strip():
            return {"error": "Text to synthesize cannot be empty"}

        persona = self.get_persona(persona_name)
        if not persona:
            return {"error": f"Unknown persona: {persona_name}"}
        
        # Apply SSML modifications if needed
        ssml_text = self._apply_ssml_modifications(text, persona)
        
        try:
            params = {
                'Text': ssml_text,
                'TextType': 'ssml' if ssml_text.startswith('<speak>') else 'text',
                'OutputFormat': output_format,
                'VoiceId': persona['polly_voice_id'],
                'Engine': persona.get('engine', 'neural'),
                'SampleRate': sample_rate
            }
            
            # Add language code for neural engine
            if persona.get('language'):
                params['LanguageCode'] = persona['language']
            
            response = self.polly_client.synthesize_speech(**params)
            
            # Read audio stream
            audio_data = response['AudioStream'].read()
            
            return {
                "success": True,
                "audio_data": audio_data,
                "content_type": response.get('ContentType', f'audio/{output_format}'),
                "persona": persona_name
            }
            
        except ClientError as e:
            return {"error": f"Speech synthesis failed: {e}"}
    
    def _apply_ssml_modifications(self, text: str, persona: Dict) -> str:
        """Apply SSML modifications based on persona settings"""
        
        # Check if text already has SSML
        if '<speak>' in text:
            return text
        
        # Build SSML with prosody adjustments
        ssml_parts = ['<speak>']
        
        # Add prosody tag if pitch or speed is modified
        prosody_attrs = []
        if persona.get('pitch', 0) != 0:
            pitch = persona['pitch']
            prosody_attrs.append(f'pitch="{f"+{pitch}%" if pitch > 0 else f"{pitch}%"}"')
        
        if persona.get('speed', 1.0) != 1.0:
            rate = int(persona['speed'] * 100)
            prosody_attrs.append(f'rate="{rate}%"')
        
        if prosody_attrs:
            ssml_parts.append(f'<prosody {" ".join(prosody_attrs)}>')
            ssml_parts.append(text)
            ssml_parts.append('</prosody>')
        else:
            ssml_parts.append(text)
        
        ssml_parts.append('</speak>')
        
        return ''.join(ssml_parts)
    
    async def create_custom_voice(
        self,
        db: Session,
        business_id: int,
        voice_name: str,
        base_persona: str,
        customizations: Dict
    ) -> Dict:
        """Create a custom voice configuration for a business"""
        from app.models.models import Business
        
        base = self.get_persona(base_persona)
        if not base:
            return {"error": f"Unknown base persona: {base_persona}"}
        
        # Merge customizations with base persona
        custom_voice = {
            **base,
            "name": voice_name,
            "customizations": customizations
        }
        
        # Apply custom pitch and speed
        if 'pitch' in customizations:
            custom_voice['pitch'] = base['pitch'] + customizations['pitch']
        
        if 'speed' in customizations:
            custom_voice['speed'] = base['speed'] * customizations['speed']
        
        # Save to business settings
        business = db.query(Business).filter(Business.id == business_id).first()
        if business:
            settings_dict = business.settings or {}
            voice_config = settings_dict.get('voice_config', {})
            voice_config['custom_voice'] = custom_voice
            settings_dict['voice_config'] = voice_config
            business.settings = settings_dict
            db.commit()
        
        return {
            "success": True,
            "voice_name": voice_name,
            "base_persona": base_persona,
            "configuration": custom_voice
        }
    
    async def get_business_voice(self, db: Session, business_id: int) -> Dict:
        """Get voice configuration for a business"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        
        if business and business.settings:
            voice_config = business.settings.get('voice_config', {})
            if voice_config.get('custom_voice'):
                return voice_config['custom_voice']
        
        # Return default persona based on business type
        default_persona = self.get_recommended_persona(business.type if business else 'general')
        return self.get_persona(default_persona)
    
    async def generate_greeting(
        self,
        db: Session,
        business_id: int,
        greeting_type: str = "standard"
    ) -> Dict:
        """Generate a greeting audio for a business"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        # Get voice configuration
        voice_config = await self.get_business_voice(db, business_id)
        persona_name = voice_config.get('name', 'professional')
        
        # Generate greeting text based on type and business
        greeting_text = self._generate_greeting_text(business, greeting_type)
        
        # Synthesize speech
        result = await self.synthesize_speech(greeting_text, persona_name)
        
        if result.get('success'):
            # Save to S3 for caching
            greeting_key = f"greetings/{business_id}/{greeting_type}.mp3"
            try:
                self.s3_client.put_object(
                    Bucket=self.voice_bucket,
                    Key=greeting_key,
                    Body=result['audio_data'],
                    ContentType='audio/mpeg'
                )
                
                return {
                    "success": True,
                    "greeting_key": greeting_key,
                    "text": greeting_text,
                    "persona": persona_name,
                    "audio_data": result['audio_data']
                }
            except ClientError as e:
                return {"error": f"Failed to save greeting: {e}"}
        
        return result
    
    def _generate_greeting_text(self, business, greeting_type: str) -> str:
        """Generate greeting text based on business and type"""
        business_name = business.name
        business_type = business.type
        
        greetings = {
            "standard": f"Thank you for calling {business_name}. How may I help you today?",
            "after_hours": f"Thank you for calling {business_name}. We are currently closed. Please leave a message after the tone, and we'll get back to you as soon as possible.",
            "holiday": f"Thank you for calling {business_name}. We are closed for the holiday. Please leave a message, and we'll return your call when we reopen.",
            "busy": f"Thank you for calling {business_name}. All our representatives are currently busy. Please hold, and someone will be with you shortly.",
            "voicemail": f"You have reached {business_name}. Please leave your name, number, and a brief message after the tone."
        }
        
        # Industry-specific greetings
        if business_type == "medical":
            greetings["standard"] = f"Thank you for calling {business_name}. If this is a medical emergency, please hang up and dial 911. Otherwise, how may I assist you today?"
        elif business_type == "restaurant":
            greetings["standard"] = f"Thank you for calling {business_name}. Would you like to place an order, make a reservation, or do you have a question?"
        
        return greetings.get(greeting_type, greetings["standard"])
    
    async def list_polly_voices(self, language_code: str = None) -> List[Dict]:
        """List available Polly voices"""
        try:
            params = {}
            if language_code:
                params['LanguageCode'] = language_code
            
            response = self.polly_client.describe_voices(**params)
            
            return [
                {
                    "id": voice['Id'],
                    "name": voice['Name'],
                    "language": voice['LanguageCode'],
                    "gender": voice['Gender'],
                    "engines": voice.get('SupportedEngines', [])
                }
                for voice in response.get('Voices', [])
            ]
            
        except ClientError as e:
            return []
    
    async def create_voice_sample(
        self,
        text: str = "Hello! This is a sample of my voice. Thank you for calling.",
        persona_name: str = "professional"
    ) -> Dict:
        """Create a voice sample for testing"""
        return await self.synthesize_speech(text, persona_name)
    
    async def get_voice_analytics(
        self,
        db: Session,
        business_id: int,
        days: int = 30
    ) -> Dict:
        """Get voice usage analytics"""
        from app.models.models import CallSession
        from sqlalchemy import func
        
        # This would track voice usage, but for now return placeholder
        return {
            "period_days": days,
            "total_synthesis_calls": 0,
            "most_used_persona": "professional",
            "average_audio_duration_seconds": 0,
            "personas_used": []
        }


# Singleton instance
voice_cloning_service = VoiceCloningService()
