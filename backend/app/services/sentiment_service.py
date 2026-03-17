"""
Sentiment Analysis Service
Analyzes call sentiment using Amazon Nova for AI-powered semantic analysis
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import re
import json
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class SentimentService:
    """Service for analyzing call sentiment with AI-powered semantic analysis"""
    
    def __init__(self):
        # Initialize Bedrock client for Nova
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
        
        # Fallback keywords for when AI is unavailable
        self.positive_keywords = [
            "thank", "thanks", "great", "excellent", "wonderful", "happy", 
            "love", "perfect", "awesome", "amazing", "good", "nice", "helpful"
        ]
        self.negative_keywords = [
            "bad", "terrible", "awful", "horrible", "angry", "frustrated",
            "disappointed", "poor", "worst", "hate", "problem", "issue", "complaint"
        ]
    
    async def analyze_text_ai(self, text: str, context: str = "") -> Dict:
        """
        AI-powered sentiment analysis using Nova.
        Provides nuanced understanding including emotions, urgency, and intent.
        """
        try:
            system_prompt = """You are a sentiment analysis expert. Analyze the text and return a JSON response with:
{
    "sentiment": "positive" | "negative" | "neutral" | "mixed",
    "confidence": 0.0-1.0,
    "emotions": ["emotion1", "emotion2"],
    "urgency": "low" | "medium" | "high",
    "customer_intent": "booking" | "inquiry" | "complaint" | "purchase" | "cancellation" | "other",
    "satisfaction_prediction": 0.0-1.0,
    "escalation_recommended": true/false,
    "key_phrases": ["phrase1", "phrase2"],
    "explanation": "Brief explanation of the analysis"
}

Emotions can include: happy, satisfied, frustrated, angry, confused, anxious, excited, disappointed, grateful, impatient"""

            user_message = f"""Analyze this customer message{' in context of: ' + context if context else ''}:

Text: "{text}"

Return only valid JSON."""

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [{"role": "user", "content": [{"text": user_message}]}],
                    "system": [{"text": system_prompt}],
                    "inferenceConfig": {
                        "maxTokens": 500,
                        "temperature": 0.1,
                        "topP": 0.9
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            content = result.get('output', {}).get('message', {}).get('content', [{}])
            response_text = content[0].get('text', '{}')
            
            # Parse AI response
            try:
                analysis = json.loads(response_text)
                return {
                    "sentiment": analysis.get("sentiment", "neutral"),
                    "confidence": round(analysis.get("confidence", 0.5), 2),
                    "score": self._sentiment_to_score(analysis.get("sentiment", "neutral")),
                    "emotions": analysis.get("emotions", []),
                    "urgency": analysis.get("urgency", "low"),
                    "customer_intent": analysis.get("customer_intent", "other"),
                    "satisfaction_prediction": round(analysis.get("satisfaction_prediction", 0.5), 2),
                    "escalation_recommended": analysis.get("escalation_recommended", False),
                    "key_phrases": analysis.get("key_phrases", []),
                    "explanation": analysis.get("explanation", ""),
                    "method": "ai_nova"
                }
            except json.JSONDecodeError:
                # Fallback to keyword analysis if AI response is malformed
                return self._fallback_analyze(text)
                
        except (ClientError, Exception) as e:
            print(f"[Sentiment] AI analysis failed, using fallback: {e}")
            return self._fallback_analyze(text)
    
    def _sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment to numeric score"""
        mapping = {"positive": 0.8, "neutral": 0.5, "negative": 0.2, "mixed": 0.5}
        return mapping.get(sentiment, 0.5)
    
    def _fallback_analyze(self, text: str) -> Dict:
        """Fallback keyword-based analysis when AI is unavailable"""
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if any(kw in word for kw in self.positive_keywords))
        negative_count = sum(1 for word in words if any(kw in word for kw in self.negative_keywords))
        
        total = positive_count + negative_count
        
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
        
        # Detect urgency
        urgency_keywords = ["urgent", "emergency", "asap", "immediately", "critical", "now"]
        urgency = "high" if any(kw in text_lower for kw in urgency_keywords) else "low"
        
        return {
            "sentiment": sentiment,
            "confidence": 0.6,
            "score": round(score, 2),
            "emotions": [],
            "urgency": urgency,
            "customer_intent": "other",
            "satisfaction_prediction": round(score, 2),
            "escalation_recommended": sentiment == "negative",
            "key_phrases": [],
            "explanation": "Fallback keyword analysis",
            "method": "keyword_fallback"
        }
    
    def analyze_text(self, text: str) -> Dict:
        """Legacy synchronous method - uses keyword fallback"""
        return self._fallback_analyze(text)
    
    async def analyze_call_sentiment(self, db: Session, call_id: str) -> Dict:
        """Analyze sentiment for a specific call using AI"""
        from app.models.models import CallSession
        
        call = db.query(CallSession).filter(CallSession.id == call_id).first()
        if not call:
            return {"error": "Call not found"}
        
        # Analyze from transcript or summary
        # Use getattr for transcript since the model may not have this field
        text_to_analyze = ""
        transcript = getattr(call, 'transcript', None)
        if transcript:
            text_to_analyze = transcript
        elif call.summary:
            text_to_analyze = call.summary
        
        if not text_to_analyze:
            return {"error": "No text to analyze"}
        
        # Use AI analysis
        result = await self.analyze_text_ai(text_to_analyze, context="phone call")
        
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
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
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
        mixed = sum(1 for c in calls if c.sentiment == "mixed")
        
        return {
            "total_calls": total,
            "period_days": days,
            "sentiment_distribution": {
                "positive": {"count": positive, "percentage": round(positive / total * 100, 1)},
                "negative": {"count": negative, "percentage": round(negative / total * 100, 1)},
                "neutral": {"count": neutral, "percentage": round(neutral / total * 100, 1)},
                "mixed": {"count": mixed, "percentage": round(mixed / total * 100, 1)}
            },
            "average_sentiment_score": round(sum(
                self._sentiment_to_score(c.sentiment) for c in calls
            ) / total, 2),
            "trend": self._calculate_sentiment_trend(calls)
        }
    
    def _calculate_sentiment_trend(self, calls: List) -> str:
        """Calculate sentiment trend over time"""
        if len(calls) < 5:
            return "insufficient_data"
        
        # Sort by time and split into two halves
        sorted_calls = sorted(calls, key=lambda c: c.start_time)
        mid = len(sorted_calls) // 2
        
        first_half_avg = sum(self._sentiment_to_score(c.sentiment) for c in sorted_calls[:mid]) / mid
        second_half_avg = sum(self._sentiment_to_score(c.sentiment) for c in sorted_calls[mid:]) / (len(sorted_calls) - mid)
        
        diff = second_half_avg - first_half_avg
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"
    
    async def analyze_realtime(self, text: str) -> Dict:
        """Real-time AI sentiment analysis for live calls"""
        result = await self.analyze_text_ai(text, context="live call")
        return result

    async def detect_vocal_emotion(self, audio_data: bytes) -> Dict:
        """
        Analyze vocal characteristics (pitch, tone, speed) to detect emotion.
        Complements text-based sentiment analysis with acoustic cues.
        """
        # In a production environment, this would use a specialized acoustic model 
        # or Amazon Transcribe's call analytics features.
        # For the prototype, we simulate detection of high-intensity vocal cues.
        
        # Simulated analysis results based on audio characteristics
        return {
            "vocal_intensity": "medium",
            "detected_emotions": ["calm"],
            "vocal_urgency": 0.3,
            "tone_stability": 0.9,
            "speech_rate_wpm": 140
        }
    
    # ==================== CALL QUALITY SCORING ====================
    
    async def calculate_call_quality_score(
        self, 
        db: Session, 
        call_id: str,
        include_transcript_analysis: bool = True
    ) -> Dict:
        """
        Calculate comprehensive call quality score.
        Includes: sentiment, resolution, efficiency, customer satisfaction prediction.
        """
        from app.models.models import CallSession, ConversationMessage
        
        call = db.query(CallSession).filter(CallSession.id == call_id).first()
        if not call:
            return {"error": "Call not found"}
        
        scores = {}
        
        # 1. Sentiment Score (0-100)
        # Use getattr for transcript since the model may not have this field
        call_transcript = getattr(call, 'transcript', None)
        if call_transcript and include_transcript_analysis:
            sentiment_result = await self.analyze_text_ai(call_transcript, context="call quality assessment")
            scores["sentiment"] = {
                "score": int(sentiment_result.get("score", 0.5) * 100),
                "sentiment": sentiment_result.get("sentiment"),
                "emotions": sentiment_result.get("emotions", [])
            }
        else:
            scores["sentiment"] = {"score": 50, "sentiment": call.sentiment or "neutral", "emotions": []}
        
        # 2. Resolution Score (0-100)
        resolution_score = self._calculate_resolution_score(call)
        scores["resolution"] = {
            "score": resolution_score,
            "intent_identified": call.intent is not None,
            "action_taken": call.action_taken is not None
        }
        
        # 3. Efficiency Score (0-100)
        efficiency_score = self._calculate_efficiency_score(call)
        scores["efficiency"] = {
            "score": efficiency_score,
            "duration_seconds": (call.end_time - call.start_time).total_seconds() if call.end_time and call.start_time else 0,
            "turn_count": db.query(ConversationMessage).filter(ConversationMessage.call_session_id == call_id).count()
        }
        
        # 4. Customer Satisfaction Prediction (0-100)
        satisfaction_score = await self._predict_satisfaction(call, db)
        scores["satisfaction_prediction"] = {
            "score": satisfaction_score,
            "confidence": 0.75
        }
        
        # Calculate overall quality score
        weights = {"sentiment": 0.25, "resolution": 0.35, "efficiency": 0.15, "satisfaction_prediction": 0.25}
        overall_score = sum(scores[k]["score"] * weights[k] for k in weights)
        
        # Determine quality grade
        if overall_score >= 85:
            grade = "A"
        elif overall_score >= 70:
            grade = "B"
        elif overall_score >= 55:
            grade = "C"
        elif overall_score >= 40:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "call_id": call_id,
            "overall_score": round(overall_score, 1),
            "grade": grade,
            "scores": scores,
            "improvement_suggestions": self._generate_improvement_suggestions(scores),
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_resolution_score(self, call) -> int:
        """Calculate how well the call was resolved"""
        score = 50  # Base score
        
        # Positive indicators
        if call.action_taken:
            score += 15
        if call.summary and len(call.summary) > 50:
            score += 10
        if call.appointment_id:
            score += 15
        if hasattr(call, 'order_id') and call.order_id:
            score += 15
        
        # Negative indicators
        if call.status == "abandoned":
            score -= 30
        if call.transfer_requested:
            score -= 10  # Needed human escalation
        
        return max(0, min(100, score))
    
    def _calculate_efficiency_score(self, call) -> int:
        """Calculate call efficiency score"""
        if not call.start_time:
            return 50
        
        duration = (call.end_time - call.start_time).total_seconds() if call.end_time else 120
        
        # Optimal call duration is 60-180 seconds
        if 60 <= duration <= 180:
            score = 100
        elif 180 < duration <= 300:
            score = 80
        elif 30 <= duration < 60:
            score = 70
        elif duration > 300:
            score = max(50, 100 - (duration - 300) / 10)
        else:
            score = 60  # Very short calls
        
        return int(score)
    
    async def _predict_satisfaction(self, call, db: Session) -> int:
        """Predict customer satisfaction using AI"""
        # Use getattr for transcript since the model may not have this field
        call_transcript = getattr(call, 'transcript', None)
        if not call_transcript:
            return 50
        
        try:
            system_prompt = """Predict customer satisfaction based on the call transcript.
Return a JSON object with: {"satisfaction_score": 0-100, "factors": ["factor1", "factor2"]}
Consider: issue resolution, tone, wait time mentions, repeated requests, gratitude expressions."""

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [{"role": "user", "content": [{"text": f"Transcript:\n{call_transcript[:2000]}"}]}],
                    "system": [{"text": system_prompt}],
                    "inferenceConfig": {"maxTokens": 200, "temperature": 0.1}
                })
            )
            
            result = json.loads(response['body'].read())
            content = result.get('output', {}).get('message', {}).get('content', [{}])
            response_text = content[0].get('text', '{"satisfaction_score": 50}')
            
            analysis = json.loads(response_text)
            return int(analysis.get("satisfaction_score", 50))
            
        except Exception as e:
            print(f"[Quality] Satisfaction prediction failed: {e}")
            return 50
    
    def _generate_improvement_suggestions(self, scores: Dict) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []
        
        if scores["sentiment"]["score"] < 60:
            suggestions.append("Consider using more empathetic language and active listening techniques")
        
        if scores["resolution"]["score"] < 60:
            suggestions.append("Focus on understanding customer intent early in the conversation")
        
        if scores["efficiency"]["score"] < 60:
            suggestions.append("Streamline the conversation flow to reduce call duration")
        
        if scores["satisfaction_prediction"]["score"] < 60:
            suggestions.append("Ensure customer concerns are fully addressed before ending the call")
        
        if not suggestions:
            suggestions.append("Great call! Continue maintaining high quality standards")
        
        return suggestions
    
    async def get_quality_trends(self, db: Session, business_id: int, days: int = 30) -> Dict:
        """Get call quality trends over time"""
        from app.models.models import CallSession
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.start_time >= start_date,
            CallSession.end_time.isnot(None)
        ).order_by(CallSession.start_time).all()
        
        if not calls:
            return {"error": "No completed calls found"}
        
        # Calculate quality scores for each call
        daily_scores = {}
        for call in calls:
            date_key = call.start_time.strftime("%Y-%m-%d")
            if date_key not in daily_scores:
                daily_scores[date_key] = {"scores": [], "count": 0}
            
            # Quick score calculation (without full AI analysis)
            quick_score = self._calculate_resolution_score(call) * 0.5 + self._calculate_efficiency_score(call) * 0.5
            daily_scores[date_key]["scores"].append(quick_score)
            daily_scores[date_key]["count"] += 1
        
        # Calculate daily averages
        trend_data = []
        for date, data in sorted(daily_scores.items()):
            avg_score = sum(data["scores"]) / len(data["scores"])
            trend_data.append({
                "date": date,
                "average_score": round(avg_score, 1),
                "call_count": data["count"]
            })
        
        # Calculate overall trend
        if len(trend_data) >= 2:
            first_week_avg = sum(d["average_score"] for d in trend_data[:7]) / min(7, len(trend_data))
            last_week_avg = sum(d["average_score"] for d in trend_data[-7:]) / min(7, len(trend_data))
            trend = "improving" if last_week_avg > first_week_avg + 5 else "declining" if last_week_avg < first_week_avg - 5 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "business_id": business_id,
            "period_days": days,
            "trend": trend,
            "daily_data": trend_data,
            "total_calls_analyzed": len(calls)
        }


sentiment_service = SentimentService()
