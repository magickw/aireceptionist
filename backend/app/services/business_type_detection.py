"""NLP-based business type detection from business description"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.models import BusinessTypeSuggestion
import re


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
        if not description:
            return [("general", 0.0)]
        
        # Normalize description
        description_lower = description.lower()
        
        # Get all active suggestions
        suggestions = db.query(BusinessTypeSuggestion).filter(
            BusinessTypeSuggestion.is_active == True
        ).all()
        
        scores = []
        
        for suggestion in suggestions:
            score = self._calculate_score(
                description_lower,
                suggestion.keywords,
                suggestion.phrases,
                suggestion.confidence_weight
            )
            if score > 0:
                scores.append((suggestion.business_type, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # If no matches, return general
        if not scores:
            return [("general", 0.0)]
        
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