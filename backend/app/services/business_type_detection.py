"""NLP-based business type detection from business description"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.models import BusinessTypeSuggestion
from app.services.nova_service import nova_service
from app.services.business_templates import BusinessTypeTemplate
import re
import json
import logging

logger = logging.getLogger(__name__)


class BusinessTypeDetector:
    """Detects business type from description using keyword and phrase matching"""
    
    def __init__(self):
        self._cache = {}
    
    def detect_from_description(
        self,
        description: str,
        db: Session
    ) -> List[Tuple[str, float]]:
        """
        Detect business type from description.
        
        Returns list of (business_type, confidence_score) tuples sorted by confidence.
        """
        # Keyword-based detection (fallback or complementary)
        return self._detect_keyword_based(description, db)

    def detect_from_description_llm(
        self,
        description: str,
        db: Session
    ) -> List[Tuple[str, float]]:
        """
        Uses LLM (Amazon Nova) to detect business type with higher reasoning.
        """
        if not description or len(description) < 10:
            return self.detect_from_description(description, db)

        available_types = BusinessTypeTemplate.get_all_types()
        
        prompt = f"""
Analyze the following business description and categorize it into the most appropriate business type from the provided list.
Provide a confidence score (0.0 to 1.0) for the top match.

Available Types: {", ".join(available_types)}

Business Description: "{description}"

Respond ONLY with a JSON object in this format:
{{"top_match": "type_key", "confidence": 0.95, "reasoning": "brief explanation"}}
"""
        try:
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            response = nova_service.bedrock_runtime.converse(
                modelId=nova_service.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.0} # Low temperature for classification
            )
            
            content = response['output']['message']['content'][0]['text']
            # Clean JSON from potential markdown blocks
            content = re.sub(r'```json\s*|\s*```', '', content).strip()
            result = json.loads(content)
            
            type_key = result.get("top_match", "general")
            confidence = float(result.get("confidence", 0.0))
            
            if type_key in available_types:
                return [(type_key, confidence)]
            return [("general", 0.1)]
            
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            return self.detect_from_description(description, db)

    def _detect_keyword_based(
        self,
        description: str,
        db: Session
    ) -> List[Tuple[str, float]]:
        """
        Keyword and phrase-based detection of business type.
        
        Returns list of (business_type, confidence_score) tuples sorted by confidence.
        """
        if not description:
            return [("general", 0.1)]
        
        desc_lower = description.lower()
        scores = []
        
        # Define keywords and phrases for each business type
        business_patterns = {
            "restaurant": {
                "keywords": ["restaurant", "food", "dining", "eatery", "cafe", "bistro", "grill", "kitchen", "cuisine", "menu", "chef", "dinner", "lunch", "breakfast", "takeout", "delivery", "catering"],
                "phrases": ["serve food", "food service", "dining experience", "catering service", "restaurant business", "eatery", "fine dining", "fast food"],
                "weight": 1.2
            },
            "hotel": {
                "keywords": ["hotel", "motel", "inn", "lodging", "accommodation", "hospitality", "resort", "boutique hotel", "bed and breakfast", "bnb", "guest house"],
                "phrases": ["overnight stay", "room booking", "hotel rooms", "guest accommodation", "hospitality business", "lodging facility"],
                "weight": 1.2
            },
            "dental": {
                "keywords": ["dental", "dentist", "orthodontist", "teeth", "tooth", "dental care", "dental clinic", "smile", "braces", "oral health", "dental hygiene"],
                "phrases": ["dental practice", "teeth cleaning", "dental services", "oral care", "dental office"],
                "weight": 1.3
            },
            "medical": {
                "keywords": ["medical", "clinic", "doctor", "physician", "healthcare", "hospital", "health center", "primary care", "urgent care", "medical practice"],
                "phrases": ["medical practice", "healthcare provider", "medical clinic", "doctor's office", "health services"],
                "weight": 1.3
            },
            "law_firm": {
                "keywords": ["law", "legal", "attorney", "lawyer", "law firm", "legal services", "litigation", "practice of law", "legal counsel", "juris doctor"],
                "phrases": ["legal practice", "law office", "attorney at law", "legal representation", "law firm"],
                "weight": 1.3
            },
            "salon": {
                "keywords": ["salon", "spa", "hair", "beauty", "haircut", "hairstyle", "cosmetology", "beauty salon", "day spa", "massage", "facial", "nail salon"],
                "phrases": ["hair salon", "beauty services", "spa services", "hair styling", "beauty treatments"],
                "weight": 1.2
            },
            "fitness": {
                "keywords": ["gym", "fitness", "workout", "exercise", "personal training", "fitness center", "health club", "yoga", "pilates", "crossfit", "trainer"],
                "phrases": ["fitness center", "gym membership", "personal training", "fitness classes", "workout facility"],
                "weight": 1.2
            },
            "real_estate": {
                "keywords": ["real estate", "property", "realty", "real estate agent", "broker", "real estate agency", "home sales", "property management", "realtor"],
                "phrases": ["real estate agency", "property sales", "real estate brokerage", "home listings", "property management"],
                "weight": 1.2
            },
            "hvac": {
                "keywords": ["hvac", "heating", "ventilation", "air conditioning", "climate control", "heating and cooling", "furnace", "air conditioner", "ac repair", "heating repair"],
                "phrases": ["hvac services", "heating and cooling", "climate control", "air conditioning service", "heating service"],
                "weight": 1.2
            },
            "accounting": {
                "keywords": ["accounting", "accountant", "tax", "tax preparation", "bookkeeping", "cpa", "financial", "tax return", "payroll", "tax firm"],
                "phrases": ["accounting firm", "tax preparation", "bookkeeping services", "financial services", "cpa firm"],
                "weight": 1.3
            },
            "retail": {
                "keywords": ["retail", "store", "shop", "shopping", "retail store", "merchandise", "sales", "boutique", "retail business"],
                "phrases": ["retail store", "retail business", "retail shop", "shopping store", "retail sales"],
                "weight": 1.1
            },
            "auto_repair": {
                "keywords": ["auto repair", "car repair", "mechanic", "automotive", "vehicle repair", "auto shop", "car maintenance", "auto service", "mechanic shop"],
                "phrases": ["auto repair shop", "car repair service", "automotive repair", "vehicle maintenance", "auto service center"],
                "weight": 1.2
            },
            "education": {
                "keywords": ["education", "tutoring", "learning", "school", "academic", "education center", "tutorial", "tutor", "learning center", "educational"],
                "phrases": ["tutoring center", "education services", "learning center", "academic tutoring", "educational services"],
                "weight": 1.2
            },
            "pet_services": {
                "keywords": ["pet", "grooming", "boarding", "pet care", "pet grooming", "dog", "cat", "pet services", "animal care", "veterinary"],
                "phrases": ["pet grooming", "pet boarding", "pet care services", "dog grooming", "pet services"],
                "weight": 1.2
            },
            "banking": {
                "keywords": ["bank", "banking", "financial institution", "credit union", "savings", "checking", "loan", "mortgage", "investment", "atm"],
                "phrases": ["banking services", "financial institution", "credit union", "bank branch", "banking operations"],
                "weight": 1.3
            },
            "insurance": {
                "keywords": ["insurance", "insurance company", "coverage", "policy", "premium", "insurance agency", "underwriting", "claims", "risk management"],
                "phrases": ["insurance agency", "insurance services", "insurance coverage", "insurance claims", "insurance policy"],
                "weight": 1.3
            },
            "veterinary": {
                "keywords": ["veterinary", "veterinarian", "vet", "animal hospital", "vet clinic", "animal doctor", "pet health", "animal care", "veterinary care"],
                "phrases": ["veterinary clinic", "animal hospital", "veterinary services", "vet practice", "animal healthcare"],
                "weight": 1.3
            }
        }
        
        # Calculate scores for each business type
        for business_type, patterns in business_patterns.items():
            keywords = patterns.get("keywords", [])
            phrases = patterns.get("phrases", [])
            weight = patterns.get("weight", 1.0)
            
            score = self._calculate_score(desc_lower, keywords, phrases, weight)
            
            if score > 0:
                scores.append((business_type, score))
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # If no matches, return general
        if not scores:
            return [("general", 0.1)]
        
        # Normalize scores to ensure they sum to 1.0
        total = sum(score for _, score in scores)
        if total > 0:
            normalized_scores = [(bt, score / total) for bt, score in scores]
            return normalized_scores
        
        return scores
    
    def _calculate_score(
        self,
        description: str,
        keywords: List[str],
        phrases: List[str],
        weight: float
    ) -> float:
        """Calculate confidence score based on keyword and phrase matches"""
        score = 0.0
        
        # Score keywords (each keyword match = 0.1)
        for keyword in keywords:
            if keyword.lower() in description:
                score += 0.1
        
        # Score phrases (each phrase match = 0.3)
        for phrase in phrases:
            if phrase.lower() in description:
                score += 0.3
        
        # Apply weight
        return min(score * weight, 1.0)
    
    def suggest_business_type(
        self,
        description: str,
        db: Session,
        top_n: int = 3
    ) -> List[Dict[str, any]]:
        """
        Suggest top N business types with confidence scores.
        
        Returns list of dicts with keys: business_type, confidence, name, icon
        """
        # Try LLM first if description is substantial
        if len(description) > 20:
            scores = self.detect_from_description_llm(description, db)
        else:
            scores = self.detect_from_description(description, db)
        
        suggestions = []
        for business_type, score in scores[:top_n]:
            # Get template details
            from app.models.models import BusinessTemplate
            template = db.query(BusinessTemplate).filter(
                BusinessTemplate.template_key == business_type
            ).first()
            
            suggestions.append({
                "business_type": business_type,
                "confidence": round(score, 2),
                "name": template.name if template else business_type.title(),
                "icon": template.icon if template else "business",
            })
        
        return suggestions


# Singleton instance
detector = BusinessTypeDetector()


def detect_business_type(description: str, db: Session) -> List[Tuple[str, float]]:
    """Convenience function for business type detection"""
    return detector.detect_from_description(description, db)


def suggest_business_types(description: str, db: Session, top_n: int = 3) -> List[Dict[str, any]]:
    """Convenience function for business type suggestions"""
    return detector.suggest_business_type(description, db, top_n)