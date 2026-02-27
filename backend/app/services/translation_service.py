"""
Multi-Language Translation Service
Provides real-time translation for voice calls using Amazon Translate and Nova
"""

from typing import Dict, List, Optional
import json
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class TranslationService:
    """Service for multi-language support with real-time translation"""
    
    # Supported languages with their codes
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "es": "Spanish",
        "zh": "Chinese (Mandarin)",
        "fr": "French",
        "de": "German",
        "ja": "Japanese",
        "ko": "Korean",
        "pt": "Portuguese",
        "it": "Italian",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi",
        "vi": "Vietnamese",
        "th": "Thai",
        "nl": "Dutch",
        "pl": "Polish"
    }
    
    def __init__(self):
        self.translate_client = boto3.client(
            service_name='translate',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
    
    def detect_language(self, text: str) -> Dict:
        """Detect the language of the input text"""
        try:
            response = self.translate_client.detectDominantLanguage(
                Text=text[:500]  # Limit text length for API
            )
            
            languages = response.get('Languages', [])
            if languages:
                top_language = languages[0]
                return {
                    "language_code": top_language['LanguageCode'],
                    "confidence": round(top_language['Score'], 2),
                    "language_name": self.SUPPORTED_LANGUAGES.get(
                        top_language['LanguageCode'], 
                        top_language['LanguageCode']
                    )
                }
            
            return {"language_code": "en", "confidence": 0.0, "language_name": "English"}
            
        except ClientError as e:
            print(f"[Translation] Language detection failed: {e}")
            return {"language_code": "en", "confidence": 0.0, "language_name": "English"}
    
    def translate_text(
        self, 
        text: str, 
        source_lang: str = "auto", 
        target_lang: str = "en"
    ) -> Dict:
        """
        Translate text from source language to target language.
        Uses Amazon Translate for fast, accurate translation.
        """
        try:
            # Auto-detect source language if not specified
            if source_lang == "auto":
                detected = self.detect_language(text)
                source_lang = detected["language_code"]
            
            # Skip if same language
            if source_lang == target_lang:
                return {
                    "translated_text": text,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "confidence": 1.0
                }
            
            response = self.translate_client.translate_text(
                Text=text,
                SourceLanguageCode=source_lang,
                TargetLanguageCode=target_lang
            )
            
            return {
                "translated_text": response['TranslatedText'],
                "source_language": response['SourceLanguageCode'],
                "target_language": response['TargetLanguageCode'],
                "confidence": 0.9
            }
            
        except Exception as e:
            print(f"[Translation] Translation failed: {e}")
            return {
                "translated_text": text,
                "source_language": source_lang if source_lang != "auto" else "unknown",
                "target_language": target_lang,
                "confidence": 0.0,
                "error": str(e)
            }

    def translate_transcript(self, text: str, source_lang: str = "auto") -> str:
        """Helper to translate transcript to English for logging"""
        if not text:
            return ""
        result = self.translate_text(text, source_lang=source_lang, target_lang="en")
        return result.get("translated_text", text)
    
    async def translate_for_voice(
        self, 
        text: str, 
        target_lang: str = "en",
        preserve_intent: bool = True
    ) -> Dict:
        """
        Translate text optimized for voice AI.
        Preserves intent and ensures natural-sounding output.
        """
        # First, detect source language
        detected = self.detect_language(text)
        source_lang = detected["language_code"]
        
        # If already in target language, return as-is
        if source_lang == target_lang:
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "detected_confidence": detected["confidence"]
            }
        
        # Translate
        translation_result = self.translate_text(text, source_lang, target_lang)
        
        # If preserve_intent, use Nova to refine the translation for context
        if preserve_intent and translation_result.get("confidence", 0) > 0.5:
            refined = await self._refine_translation_for_voice(
                original=text,
                translated=translation_result["translated_text"],
                source_lang=source_lang,
                target_lang=target_lang
            )
            translation_result["translated_text"] = refined
            translation_result["refined"] = True
        
        translation_result["original_text"] = text
        translation_result["detected_confidence"] = detected["confidence"]
        
        return translation_result
    
    async def _refine_translation_for_voice(
        self, 
        original: str, 
        translated: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """Use Nova to refine translation for voice context"""
        try:
            system_prompt = f"""You are a translation refiner for voice AI systems.
The following text was translated from {source_lang} to {target_lang}.
Ensure the translation:
1. Sounds natural when spoken aloud
2. Preserves the original intent and tone
3. Is appropriate for a customer service context
4. Maintains any questions or requests clearly

Return only the refined translation, nothing else."""

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [{"role": "user", "content": [{"text": translated}]}],
                    "system": [{"text": system_prompt}],
                    "inferenceConfig": {"maxTokens": 500, "temperature": 0.1}
                })
            )
            
            result = json.loads(response['body'].read())
            content = result.get('output', {}).get('message', {}).get('content', [{}])
            refined = content[0].get('text', translated)
            
            return refined.strip()
            
        except Exception as e:
            print(f"[Translation] Refinement failed: {e}")
            return translated
    
    async def generate_response_in_language(
        self, 
        response_text: str, 
        target_lang: str
    ) -> str:
        """
        Generate a response in the target language.
        Translates the AI response back to the customer's language.
        """
        if target_lang == "en":
            return response_text
        
        result = self.translate_text(response_text, "en", target_lang)
        return result.get("translated_text", response_text)
    
    def get_supported_languages(self) -> List[Dict]:
        """Get list of supported languages"""
        return [
            {"code": code, "name": name}
            for code, name in self.SUPPORTED_LANGUAGES.items()
        ]
    
    async def identify_customer_language_preference(
        self, 
        db, 
        customer_phone: str,
        business_id: int
    ) -> Optional[str]:
        """Identify customer's preferred language from call history"""
        try:
            from app.models.models import CallSession
            from sqlalchemy import func
            
            # Get language preferences from past calls
            calls = db.query(
                CallSession.detected_language,
                func.count(CallSession.id).label('count')
            ).filter(
                CallSession.business_id == business_id,
                CallSession.customer_phone == customer_phone,
                CallSession.detected_language.isnot(None)
            ).group_by(CallSession.detected_language).order_by(
                func.count(CallSession.id).desc()
            ).first()
            
            if calls:
                return calls.detected_language
            
            return None
            
        except Exception as e:
            print(f"[Translation] Could not identify language preference: {e}")
            return None
    
    def is_rtl_language(self, lang_code: str) -> bool:
        """Check if language is right-to-left"""
        rtl_languages = {"ar", "he", "fa", "ur"}
        return lang_code in rtl_languages


# Singleton instance
translation_service = TranslationService()
