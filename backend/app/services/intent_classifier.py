"""Intent Classifier - Validate and classify intents with confidence scoring"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import IntentClassification
import re
from collections import Counter


class IntentClassifier:
    """
    Classifies user intents based on training data and validates LLM-detected intents.
    Provides confidence scoring and validation to improve reasoning accuracy.
    """
    
    def __init__(self):
        self._training_cache = {}
        self._pattern_cache = {}
    
    def classify(
        self,
        user_input: str,
        business_type: str,
        db: Session
    ) -> Tuple[Optional[str], float, Dict]:
        """
        Classify the intent of user input.
        
        Args:
            user_input: User's message/text
            business_type: Type of business (e.g., 'restaurant', 'medical')
            db: Database session
        
        Returns:
            Tuple of (intent, confidence_score, entities)
        """
        if not user_input:
            return None, 0.0, {}
        
        # Normalize input
        normalized_input = self._normalize_input(user_input)
        
        # Get training data for this business type
        training_data = self._get_training_data(business_type, db)
        
        if not training_data:
            return None, 0.0, {}
        
        # Calculate scores for each intent
        intent_scores = {}
        for item in training_data:
            intent = item.intent
            example = self._normalize_input(item.user_input)
            
            # Calculate similarity score
            score = self._calculate_similarity(normalized_input, example)
            
            if score > 0:
                if intent not in intent_scores:
                    intent_scores[intent] = []
                intent_scores[intent].append({
                    "score": score,
                    "entities": item.entities
                })
        
        if not intent_scores:
            return None, 0.0, {}
        
        # Find best intent (highest average score)
        best_intent = None
        best_score = 0.0
        best_entities = {}
        
        for intent, matches in intent_scores.items():
            avg_score = sum(m["score"] for m in matches) / len(matches)
            if avg_score > best_score:
                best_score = avg_score
                best_intent = intent
                # Use entities from the best match
                best_match = max(matches, key=lambda x: x["score"])
                best_entities = best_match["entities"] or {}
        
        return best_intent, best_score, best_entities
    
    def validate_intent(
        self,
        detected_intent: str,
        user_input: str,
        business_type: str,
        db: Session,
        threshold: float = 0.6
    ) -> Tuple[bool, Optional[str], float]:
        """
        Validate an LLM-detected intent against training data.
        
        Args:
            detected_intent: Intent detected by LLM
            user_input: User's message/text
            business_type: Type of business
            db: Database session
            threshold: Minimum confidence threshold for validation
        
        Returns:
            Tuple of (is_valid, suggested_intent, confidence_score)
        """
        # Classify using training data
        classified_intent, confidence, entities = self.classify(user_input, business_type, db)
        
        if confidence < threshold:
            # Low confidence - suggest classification result if available
            return False, classified_intent, confidence
        
        # Check if LLM intent matches classification
        if classified_intent and classified_intent != detected_intent:
            # Different intent detected
            if confidence >= 0.8:
                # High confidence in different intent - suggest override
                return False, classified_intent, confidence
            else:
                # Moderate confidence - accept LLM intent
                return True, None, confidence
        
        return True, None, confidence
    
    def get_supported_intents(self, business_type: str, db: Session) -> List[str]:
        """Get list of supported intents for a business type"""
        training_data = self._get_training_data(business_type, db)
        intents = set(item.intent for item in training_data)
        return sorted(list(intents))
    
    def add_training_example(
        self,
        business_type: str,
        intent: str,
        user_input: str,
        entities: Optional[Dict] = None,
        confidence: Optional[float] = None,
        db: Session = None
    ) -> IntentClassification:
        """
        Add a training example for intent classification.
        
        Args:
            business_type: Type of business
            intent: Intent label
            user_input: Example user utterance
            entities: Extracted entities
            confidence: Expected confidence score
            db: Database session
        
        Returns:
            Created IntentClassification record
        """
        classification = IntentClassification(
            business_type=business_type,
            intent=intent,
            user_input=user_input,
            entities=entities,
            confidence=confidence,
            is_active=True
        )
        
        if db:
            db.add(classification)
            db.commit()
            db.refresh(classification)
            
            # Clear cache
            self._clear_cache(business_type)
        
        return classification
    
    def _normalize_input(self, text: str) -> str:
        """Normalize text for comparison"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove punctuation except for important symbols
        text = re.sub(r'[^\w\s$@#]', '', text)
        return text
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity score between two texts.
        Uses a combination of word overlap and sequence matching.
        """
        # Word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        word_overlap = len(intersection) / len(union) if union else 0.0
        
        # Sequence matching (longest common substring)
        lcs_length = self._longest_common_subsequence(text1, text2)
        avg_length = (len(text1) + len(text2)) / 2
        sequence_score = lcs_length / avg_length if avg_length > 0 else 0.0
        
        # Weighted average
        similarity = (word_overlap * 0.6) + (sequence_score * 0.4)
        
        return similarity
    
    def _longest_common_subsequence(self, text1: str, text2: str) -> int:
        """Calculate length of longest common subsequence"""
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        return dp[m][n]
    
    def _get_training_data(
        self,
        business_type: str,
        db: Session
    ) -> List[IntentClassification]:
        """Get training data for a business type"""
        if db is None:
            return []
            
        # Check cache
        cache_key = f"{business_type}_{db.hash_key if hasattr(db, 'hash_key') else 'default'}"
        if cache_key in self._training_cache:
            return self._training_cache[cache_key]
        
        # Query database
        training_data = db.query(IntentClassification).filter(
            IntentClassification.business_type == business_type,
            IntentClassification.is_active == True
        ).all()
        
        # Cache it
        self._training_cache[cache_key] = training_data
        
        return training_data
    
    def _clear_cache(self, business_type: str):
        """Clear cache for a business type"""
        keys_to_remove = [k for k in self._training_cache.keys() if k.startswith(business_type)]
        for key in keys_to_remove:
            del self._training_cache[key]


# Singleton instance
intent_classifier = IntentClassifier()


# Convenience functions
def classify_intent(user_input: str, business_type: str, db: Session) -> Tuple[Optional[str], float, Dict]:
    """Classify intent from user input"""
    return intent_classifier.classify(user_input, business_type, db)


def validate_intent(detected_intent: str, user_input: str, business_type: str, db: Session, threshold: float = 0.6) -> Tuple[bool, Optional[str], float]:
    """Validate an LLM-detected intent"""
    return intent_classifier.validate_intent(detected_intent, user_input, business_type, db, threshold)