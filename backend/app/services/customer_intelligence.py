"""
Customer Intelligence Service using Nova Multimodal Embeddings

This service provides:
- Multimodal embeddings for customer history semantic search
- Churn risk detection
- VIP identification
- Sentiment analysis
- Pattern recognition
"""

import boto3
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.config import settings
from app.models.models import CallSession, ConversationMessage, Appointment, User


class CustomerIntelligenceService:
    """Advanced customer analytics using Nova embeddings"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        # Using Titan Multimodal Embeddings for text analysis
        self.embedding_model = "amazon.titan-embed-text-v1"
        
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding using Nova-compatible embedding model
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.embedding_model,
                body=json.dumps({
                    "inputText": text
                })
            )
            
            result = json.loads(response["body"].read())
            return result.get("embedding", [])
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    async def index_customer_history(self, customer_phone: str, business_id: int, db: Session):
        """
        Index all customer interactions with embeddings for semantic search
        
        Args:
            customer_phone: Customer phone number
            business_id: Business ID
            db: Database session
        """
        try:
            # Get all call sessions for this customer
            call_sessions = db.query(CallSession).filter(
                CallSession.business_id == business_id,
                CallSession.customer_phone == customer_phone
            ).order_by(desc(CallSession.started_at)).all()
            
            # Generate embeddings for each transcript/message
            for session in call_sessions:
                messages = db.query(ConversationMessage).filter(
                    ConversationMessage.call_session_id == session.id
                ).all()
                
                # Combine all messages into a single text
                conversation_text = "\n".join([
                    f"{msg.sender}: {msg.content}" for msg in messages
                ])
                
                if conversation_text:
                    # Generate embedding
                    embedding = await self.generate_embedding(conversation_text)
                    
                    # Store embedding (in production, use vector database like Pinecone/Weaviate)
                    # For now, we'll store in a simple dict structure
                    if embedding:
                        # This would be stored in a vector database
                        pass
            
            return {"success": True, "indexed": len(call_sessions)}
            
        except Exception as e:
            print(f"Error indexing customer history: {e}")
            return {"success": False, "error": str(e)}
    
    async def semantic_search_customer_history(
        self, 
        query: str, 
        customer_phone: str, 
        business_id: int, 
        db: Session,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across customer history
        
        Args:
            query: Search query
            customer_phone: Customer phone number
            business_id: Business ID
            db: Database session
            top_k: Number of results to return
            
        Returns:
            List of matching interactions with relevance scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # In production, use vector database for similarity search
            # For demo, we'll do keyword-based search with scoring
            call_sessions = db.query(CallSession).filter(
                CallSession.business_id == business_id,
                CallSession.customer_phone == customer_phone
            ).order_by(desc(CallSession.started_at)).all()
            
            results = []
            for session in call_sessions:
                messages = db.query(ConversationMessage).filter(
                    ConversationMessage.call_session_id == session.id
                ).all()
                
                # Simple keyword matching for demo
                conversation_text = "\n".join([
                    f"{msg.sender}: {msg.content}" for msg in messages
                ]).lower()
                
                # Calculate simple relevance score
                score = 0
                query_words = query.lower().split()
                for word in query_words:
                    if word in conversation_text:
                        score += 1
                
                if score > 0:
                    results.append({
                        "session_id": session.id,
                        "date": session.started_at,
                        "relevance_score": min(score / len(query_words), 1.0),
                        "preview": conversation_text[:200] + "..." if len(conversation_text) > 200 else conversation_text,
                        "transcript": conversation_text
                    })
            
            # Sort by relevance and return top_k
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    async def calculate_churn_risk(
        self, 
        customer_phone: str, 
        business_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Calculate churn risk for a customer using multiple factors
        
        Factors:
        - Sentiment trend (declining = high risk)
        - Frequency of complaints
        - Time since last interaction
        - Appointment cancellation rate
        - Spending trend (if available)
        
        Returns:
            Dict with churn risk score and contributing factors
        """
        try:
            # Get recent call sessions
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_sessions = db.query(CallSession).filter(
                CallSession.business_id == business_id,
                CallSession.customer_phone == customer_phone,
                CallSession.started_at >= thirty_days_ago
            ).order_by(desc(CallSession.started_at)).all()
            
            # Get recent messages for sentiment analysis
            recent_messages = []
            for session in recent_sessions:
                messages = db.query(ConversationMessage).filter(
                    ConversationMessage.call_session_id == session.id
                ).all()
                recent_messages.extend(messages)
            
            # Calculate sentiment trend
            sentiment_scores = []
            negative_count = 0
            complaint_keywords = ['complaint', 'unhappy', 'terrible', 'worst', 'angry', 'frustrated', 'disappointed']
            
            for msg in recent_messages:
                if msg.sender == 'customer':
                    text = msg.content.lower()
                    if any(keyword in text for keyword in complaint_keywords):
                        negative_count += 1
                    
                    # Simple sentiment scoring (in production, use Nova for this)
                    sentiment = 0.5  # neutral default
                    if any(keyword in text for keyword in complaint_keywords):
                        sentiment = 0.2  # negative
                    elif any(word in text for word in ['great', 'excellent', 'happy', 'love', 'thanks']):
                        sentiment = 0.9  # positive
                    
                    sentiment_scores.append(sentiment)
            
            # Calculate metrics
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
            sentiment_trend = sentiment_scores[-1] - sentiment_scores[0] if len(sentiment_scores) > 1 else 0
            
            # Complaint frequency
            complaint_rate = negative_count / len(recent_messages) if recent_messages else 0
            
            # Time since last interaction
            last_interaction = max([s.started_at for s in recent_sessions]) if recent_sessions else None
            days_since_last = (datetime.now() - last_interaction).days if last_interaction else 999
            
            # Appointment cancellation rate
            recent_appointments = db.query(Appointment).filter(
                Appointment.business_id == business_id,
                Appointment.customer_phone == customer_phone,
                Appointment.created_at >= thirty_days_ago
            ).all()
            
            cancelled_rate = sum(1 for apt in recent_appointments if apt.status == 'cancelled') / len(recent_appointments) if recent_appointments else 0
            
            # Calculate overall churn risk (0-1)
            churn_risk = 0.0
            
            # Sentiment decline
            if sentiment_trend < -0.2:
                churn_risk += 0.3
            elif sentiment_trend < 0:
                churn_risk += 0.15
            
            # Low average sentiment
            if avg_sentiment < 0.4:
                churn_risk += 0.25
            elif avg_sentiment < 0.6:
                churn_risk += 0.10
            
            # High complaint rate
            if complaint_rate > 0.3:
                churn_risk += 0.20
            elif complaint_rate > 0.1:
                churn_risk += 0.10
            
            # No recent interaction
            if days_since_last > 60:
                churn_risk += 0.25
            elif days_since_last > 30:
                churn_risk += 0.15
            
            # High cancellation rate
            if cancelled_rate > 0.5:
                churn_risk += 0.20
            elif cancelled_rate > 0.3:
                churn_risk += 0.10
            
            # Cap at 1.0
            churn_risk = min(churn_risk, 1.0)
            
            return {
                "churn_risk_score": round(churn_risk, 2),
                "risk_level": "high" if churn_risk > 0.6 else "medium" if churn_risk > 0.3 else "low",
                "factors": {
                    "sentiment_trend": round(sentiment_trend, 2),
                    "avg_sentiment": round(avg_sentiment, 2),
                    "complaint_rate": round(complaint_rate, 2),
                    "days_since_last_interaction": days_since_last,
                    "cancellation_rate": round(cancelled_rate, 2)
                },
                "recommendations": self._get_churn_risk_recommendations(churn_risk, {
                    "sentiment_trend": sentiment_trend,
                    "complaint_rate": complaint_rate,
                    "days_since_last": days_since_last
                })
            }
            
        except Exception as e:
            print(f"Error calculating churn risk: {e}")
            return {
                "churn_risk_score": 0.5,
                "risk_level": "unknown",
                "error": str(e)
            }
    
    def _get_churn_risk_recommendations(self, churn_risk: float, factors: Dict[str, Any]) -> List[str]:
        """Get recommendations based on churn risk and factors"""
        recommendations = []
        
        if churn_risk > 0.6:
            recommendations.append("⚠️ HIGH RISK: Immediate intervention required")
            recommendations.append("Schedule personal follow-up call within 24 hours")
            recommendations.append("Offer personalized discount or incentive")
            recommendations.append("Review recent interactions for specific issues")
        elif churn_risk > 0.3:
            recommendations.append("⚡ MEDIUM RISK: Proactive engagement recommended")
            recommendations.append("Send personalized check-in message")
            recommendations.append("Consider special offer for next appointment")
            recommendations.append("Monitor sentiment in upcoming interactions")
        else:
            recommendations.append("✅ LOW RISK: Customer relationship is stable")
            recommendations.append("Continue regular engagement")
            recommendations.append("Request feedback or review to maintain satisfaction")
        
        # Specific factor-based recommendations
        if factors.get("sentiment_trend", 0) < -0.2:
            recommendations.append("Sentiment declining - investigate recent issues")
        
        if factors.get("complaint_rate", 0) > 0.2:
            recommendations.append("High complaint rate - address service quality concerns")
        
        if factors.get("days_since_last", 0) > 30:
            recommendations.append("No recent contact - re-engage with personalized outreach")
        
        return recommendations
    
    async def identify_vip_customers(
        self, 
        business_id: int, 
        db: Session,
        min_satisfaction: float = 4.5,
        min_appointments: int = 5,
        min_spend: float = 500
    ) -> List[Dict[str, Any]]:
        """
        Identify VIP customers based on multiple criteria
        
        Criteria:
        - High satisfaction score (>4.5)
        - Frequent appointments (>5)
        - High spending (>$500)
        - Long-term customer (>6 months)
        - Referral activity (if tracked)
        - Positive sentiment in interactions
        
        Returns:
            List of VIP customers with their metrics
        """
        try:
            # Get all customers who have had calls
            call_sessions = db.query(CallSession).filter(
                CallSession.business_id == business_id
            ).all()
            
            # Group by customer phone
            customer_stats = {}
            for session in call_sessions:
                phone = session.customer_phone
                if phone not in customer_stats:
                    customer_stats[phone] = {
                        "phone": phone,
                        "total_calls": 0,
                        "first_interaction": session.started_at,
                        "last_interaction": session.started_at,
                        "total_duration": 0,
                        "messages": []
                    }
                
                customer_stats[phone]["total_calls"] += 1
                customer_stats[phone]["total_duration"] += session.duration_seconds or 0
                
                if session.started_at < customer_stats[phone]["first_interaction"]:
                    customer_stats[phone]["first_interaction"] = session.started_at
                if session.started_at > customer_stats[phone]["last_interaction"]:
                    customer_stats[phone]["last_interaction"] = session.started_at
                
                # Get messages for sentiment analysis
                messages = db.query(ConversationMessage).filter(
                    ConversationMessage.call_session_id == session.id
                ).all()
                customer_stats[phone]["messages"].extend(messages)
            
            # Get appointment counts
            for phone in customer_stats:
                appointments = db.query(Appointment).filter(
                    Appointment.business_id == business_id,
                    Appointment.customer_phone == phone
                ).all()
                customer_stats[phone]["total_appointments"] = len(appointments)
                customer_stats[phone]["completed_appointments"] = sum(
                    1 for apt in appointments if apt.status == 'completed'
                )
            
            # Calculate VIP scores
            vip_customers = []
            for phone, stats in customer_stats.items():
                # Calculate satisfaction score from sentiment
                customer_messages = [m for m in stats["messages"] if m.sender == 'customer']
                sentiment_scores = []
                for msg in customer_messages:
                    text = msg.content.lower()
                    sentiment = 0.5
                    if any(word in text for word in ['great', 'excellent', 'happy', 'love', 'thanks', 'awesome']):
                        sentiment = 0.9
                    elif any(word in text for word in ['complaint', 'unhappy', 'terrible', 'worst']):
                        sentiment = 0.2
                    sentiment_scores.append(sentiment)
                
                avg_satisfaction = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 3.0
                
                # Calculate customer lifetime (months)
                lifetime_months = (datetime.now() - stats["first_interaction"]).days / 30 if stats["first_interaction"] else 0
                
                # Calculate engagement score
                engagement_score = (
                    min(stats["total_calls"] / 10, 1.0) * 0.3 +
                    min(stats["total_appointments"] / 10, 1.0) * 0.3 +
                    min(lifetime_months / 24, 1.0) * 0.2 +
                    min(avg_satisfaction / 5.0, 1.0) * 0.2
                )
                
                # VIP criteria check
                is_vip = (
                    avg_satisfaction >= min_satisfaction and
                    stats["total_appointments"] >= min_appointments and
                    engagement_score >= 0.7
                )
                
                if is_vip:
                    vip_customers.append({
                        "phone": phone,
                        "name": f"Customer {phone[-4:]}",  # Placeholder name
                        "satisfaction_score": round(avg_satisfaction, 2),
                        "total_calls": stats["total_calls"],
                        "total_appointments": stats["total_appointments"],
                        "completed_appointments": stats["completed_appointments"],
                        "lifetime_months": round(lifetime_months, 1),
                        "engagement_score": round(engagement_score, 2),
                        "vip_tier": self._get_vip_tier(engagement_score),
                        "last_interaction": stats["last_interaction"].strftime("%Y-%m-%d"),
                        "total_duration_minutes": round(stats["total_duration"] / 60, 1)
                    })
            
            # Sort by engagement score
            vip_customers.sort(key=lambda x: x["engagement_score"], reverse=True)
            
            return vip_customers
            
        except Exception as e:
            print(f"Error identifying VIP customers: {e}")
            return []
    
    def _get_vip_tier(self, engagement_score: float) -> str:
        """Get VIP tier based on engagement score"""
        if engagement_score >= 0.9:
            return "PLATINUM"
        elif engagement_score >= 0.8:
            return "GOLD"
        elif engagement_score >= 0.7:
            return "SILVER"
        else:
            return "BRONZE"
    
    async def detect_complaint_patterns(
        self, 
        business_id: int, 
        db: Session,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Detect patterns in customer complaints
        
        Analyzes:
        - Common complaint topics
        - Trending issues
        - Escalation patterns
        - Resolution rates
        
        Returns:
            Dict with pattern analysis
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get recent call sessions
            recent_sessions = db.query(CallSession).filter(
                CallSession.business_id == business_id,
                CallSession.started_at >= cutoff_date
            ).all()
            
            complaint_keywords = {
                'wait_time': ['wait', 'waited', 'waiting', 'delay', 'late'],
                'service_quality': ['service', 'quality', 'terrible', 'poor', 'bad'],
                'staff': ['staff', 'rude', 'unprofessional', 'attitude'],
                'price': ['expensive', 'price', 'cost', 'overpriced'],
                'scheduling': ['schedule', 'appointment', 'booking', 'cancelled'],
                'communication': ['call back', 'never called', 'no response', 'ignored']
            }
            
            # Analyze messages for complaints
            complaint_topics = {topic: 0 for topic in complaint_keywords.keys()}
            total_complaints = 0
            
            for session in recent_sessions:
                messages = db.query(ConversationMessage).filter(
                    ConversationMessage.call_session_id == session.id
                ).all()
                
                for msg in messages:
                    if msg.sender == 'customer':
                        text = msg.content.lower()
                        
                        # Check for complaint keywords
                        is_complaint = False
                        for topic, keywords in complaint_keywords.items():
                            if any(keyword in text for keyword in keywords):
                                complaint_topics[topic] += 1
                                is_complaint = True
                        
                        if is_complaint:
                            total_complaints += 1
            
            # Calculate patterns
            top_issues = sorted(
                complaint_topics.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            return {
                "total_complaints": total_complaints,
                "complaint_rate": round(total_complaints / len(recent_sessions), 3) if recent_sessions else 0,
                "top_issues": [
                    {"topic": topic, "count": count, "percentage": round(count / total_complaints * 100, 1) if total_complaints > 0 else 0}
                    for topic, count in top_issues if count > 0
                ],
                "recommendations": self._get_complaint_pattern_recommendations(top_issues)
            }
            
        except Exception as e:
            print(f"Error detecting complaint patterns: {e}")
            return {"error": str(e)}
    
    def _get_complaint_pattern_recommendations(self, top_issues: List[tuple]) -> List[str]:
        """Get recommendations based on complaint patterns"""
        recommendations = []
        
        if not top_issues or top_issues[0][1] == 0:
            return ["No significant complaint patterns detected"]
        
        # Add recommendations based on top issue
        for issue, count in top_issues[:3]:
            if count > 0:
                if issue == 'wait_time':
                    recommendations.append("Address wait time concerns - optimize scheduling")
                elif issue == 'service_quality':
                    recommendations.append("Review service quality standards and training")
                elif issue == 'staff':
                    recommendations.append("Evaluate staff training and professionalism")
                elif issue == 'price':
                    recommendations.append("Review pricing strategy and value proposition")
                elif issue == 'scheduling':
                    recommendations.append("Improve scheduling system and appointment reminders")
                elif issue == 'communication':
                    recommendations.append("Enhance communication protocols and follow-up procedures")
        
        return recommendations


# Singleton instance
customer_intelligence_service = CustomerIntelligenceService()