"""
Sentiment Analysis Service
Analyzes call sentiment using Amazon Nova
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import re


class SentimentService:
    """Service for analyzing call sentiment"""
    
    def __init__(self):
        self.positive_keywords = [
            "thank", "thanks", "great", "excellent", "wonderful", "happy", 
            "love", "perfect", "awesome", "amazing", "good", "nice", "helpful"
        ]
        self.negative_keywords = [
            "bad", "terrible", "awful", "horrible", "angry", "frustrated",
            "disappointed", "poor", "worst", "hate", "problem", "issue", "complaint"
        ]
        self.neutral_keywords = [
            "okay", "alright", "fine", "sure", "yes", "no", "maybe"
        ]
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment of text"""
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if any(kw in word for kw in self.positive_keywords))
        negative_count = sum(1 for word in words if any(kw in word for kw in self.negative_keywords))
        neutral_count = sum(1 for word in words if any(kw in word for kw in self.neutral_keywords))
        
        total = positive_count + negative_count + neutral_count
        
        if total == 0:
            score = 0.5
            sentiment = "neutral"
        else:
            score = (positive_count - negative_count + total) / (2 * total)
            
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "keywords": {
                "positive": [w for w in words if any(kw in w for kw in self.positive_keywords)],
                "negative": [w for w in words if any(kw in w for kw in self.negative_keywords)]
            }
        }
    
    def analyze_call_sentiment(self, db: Session, call_id: int) -> Dict:
        """Analyze sentiment for a specific call"""
        from app.models.models import CallSession
        
        call = db.query(CallSession).filter(CallSession.id == call_id).first()
        if not call:
            return {"error": "Call not found"}
        
        # Analyze from transcript or summary
        text_to_analyze = ""
        if call.transcript:
            text_to_analyze = call.transcript
        elif call.summary:
            text_to_analyze = call.summary
        
        if not text_to_analyze:
            return {"error": "No text to analyze"}
        
        result = self.analyze_text(text_to_analyze)
        
        # Update call record
        call.sentiment = result["sentiment"]
        db.commit()
        
        return {
            "call_id": call_id,
            **result
        }
    
    def get_business_sentiment_stats(
        self, 
        db: Session, 
        business_id: int, 
        days: int = 30
    ) -> Dict:
        """Get aggregated sentiment statistics for a business"""
        from app.models.models import CallSession
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.start_time >= start_date,
            CallSession.sentiment.isnot(None)
        ).all()
        
        total = len(calls)
        if total == 0:
            return {"total_calls": 0, "sentiment_distribution": {}}
        
        positive = sum(1 for c in calls if c.sentiment == "positive")
        negative = sum(1 for c in calls if c.sentiment == "negative")
        neutral = sum(1 for c in calls if c.sentiment == "neutral")
        
        return {
            "total_calls": total,
            "period_days": days,
            "sentiment_distribution": {
                "positive": {"count": positive, "percentage": round(positive / total * 100, 1)},
                "negative": {"count": negative, "percentage": round(negative / total * 100, 1)},
                "neutral": {"count": neutral, "percentage": round(neutral / total * 100, 1)}
            },
            "average_sentiment_score": round(sum(
                self._sentiment_to_score(c.sentiment) for c in calls
            ) / total, 2)
        }
    
    def _sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment to numeric score"""
        mapping = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
        return mapping.get(sentiment, 0.5)
    
    def analyze_realtime(self, text: str) -> Dict:
        """Real-time sentiment analysis for live calls"""
        result = self.analyze_text(text)
        
        # Add urgency detection
        urgency_keywords = ["urgent", "emergency", "asap", "immediately", "critical"]
        urgency = any(kw in text.lower() for kw in urgency_keywords)
        
        result["urgency_detected"] = urgency
        
        return result


sentiment_service = SentimentService()
