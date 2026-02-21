"""
Customer 360 Service
Unified customer profiles with lifetime value calculation and personalized insights
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from decimal import Decimal
import json
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class Customer360Service:
    """Service for Customer 360 view - unified customer intelligence"""
    
    # Loyalty tier thresholds
    LOYALTY_TIERS = {
        "platinum": {"min_spend": 5000, "min_interactions": 50},
        "gold": {"min_spend": 2000, "min_interactions": 25},
        "silver": {"min_spend": 500, "min_interactions": 10},
        "standard": {"min_spend": 0, "min_interactions": 0}
    }
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
    
    async def get_customer_profile(
        self,
        db: Session,
        business_id: int,
        customer_phone: str
    ) -> Dict:
        """Get complete 360-degree view of a customer"""
        from app.models.models import Customer, CallSession, Order, Appointment
        
        # Find or create customer
        customer = db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.phone == customer_phone
        ).first()
        
        if not customer:
            return {"error": "Customer not found", "phone": customer_phone}
        
        # Get all related data
        calls = db.query(CallSession).filter(
            CallSession.customer_id == customer.id
        ).order_by(CallSession.started_at.desc()).limit(10).all()
        
        orders = db.query(Order).filter(
            Order.customer_id == customer.id
        ).order_by(Order.created_at.desc()).limit(10).all()
        
        appointments = db.query(Appointment).filter(
            Appointment.customer_id == customer.id
        ).order_by(Appointment.appointment_time.desc()).limit(10).all()
        
        # Calculate lifetime value
        ltv = await self._calculate_lifetime_value(db, customer)
        
        # Generate insights
        insights = await self._generate_customer_insights(db, customer)
        
        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "preferred_language": customer.preferred_language,
                "loyalty_tier": customer.loyalty_tier,
                "is_vip": customer.is_vip,
                "customer_since": customer.customer_since.isoformat() if customer.customer_since else None,
                "last_interaction": customer.last_interaction.isoformat() if customer.last_interaction else None,
                "tags": customer.tags or [],
                "notes": customer.notes
            },
            "metrics": {
                "total_calls": customer.total_calls,
                "total_orders": customer.total_orders,
                "total_appointments": customer.total_appointments,
                "total_spent": float(customer.total_spent) if customer.total_spent else 0,
                "lifetime_value": ltv,
                "average_sentiment": float(customer.avg_sentiment) if customer.avg_sentiment else 0.5,
                "average_quality_score": float(customer.avg_quality_score) if customer.avg_quality_score else 50,
                "churn_risk": float(customer.churn_risk) if customer.churn_risk else 0
            },
            "recent_activity": {
                "calls": [
                    {
                        "id": c.id,
                        "date": c.started_at.isoformat() if c.started_at else None,
                        "duration_seconds": c.duration_seconds,
                        "sentiment": c.sentiment,
                        "quality_score": float(c.quality_score) if c.quality_score else None,
                        "summary": c.summary[:100] + "..." if c.summary and len(c.summary) > 100 else c.summary
                    }
                    for c in calls
                ],
                "orders": [
                    {
                        "id": o.id,
                        "date": o.created_at.isoformat() if o.created_at else None,
                        "total": float(o.total_amount) if o.total_amount else 0,
                        "status": o.status
                    }
                    for o in orders
                ],
                "appointments": [
                    {
                        "id": a.id,
                        "date": a.appointment_time.isoformat() if a.appointment_time else None,
                        "service": a.service_type,
                        "status": a.status
                    }
                    for a in appointments
                ]
            },
            "insights": insights,
            "recommendations": await self._get_personalized_recommendations(customer, ltv)
        }
    
    async def _calculate_lifetime_value(self, db: Session, customer) -> Dict:
        """Calculate customer lifetime value with projections"""
        from app.models.models import Order
        
        # Historical value
        historical_value = float(customer.total_spent or 0)
        
        # Get order history for trend analysis
        orders = db.query(Order).filter(
            Order.customer_id == customer.id
        ).order_by(Order.created_at).all()
        
        if not orders:
            return {
                "historical": 0,
                "projected_12_month": 0,
                "confidence": 0
            }
        
        # Calculate average order value
        avg_order_value = historical_value / len(orders) if orders else 0
        
        # Calculate order frequency (orders per month)
        if len(orders) >= 2:
            first_order = orders[0].created_at
            last_order = orders[-1].created_at
            months_active = max(1, (last_order - first_order).days / 30)
            orders_per_month = len(orders) / months_active
        else:
            orders_per_month = 0.5  # Assume one order every 2 months
        
        # Project 12-month value
        projected_12_month = avg_order_value * orders_per_month * 12
        
        # Apply retention factor based on churn risk
        churn_risk = float(customer.churn_risk or 0.2)
        retention_factor = 1 - churn_risk
        projected_12_month *= retention_factor
        
        return {
            "historical": round(historical_value, 2),
            "projected_12_month": round(projected_12_month, 2),
            "average_order_value": round(avg_order_value, 2),
            "orders_per_month": round(orders_per_month, 2),
            "confidence": min(1.0, len(orders) / 10)  # More orders = more confident
        }
    
    async def _generate_customer_insights(self, db: Session, customer) -> List[Dict]:
        """Generate AI-powered insights about customer"""
        from app.models.models import CallSession, Order
        
        insights = []
        
        # Sentiment trend insight
        if customer.avg_sentiment:
            if float(customer.avg_sentiment) < 0.4:
                insights.append({
                    "type": "warning",
                    "category": "satisfaction",
                    "message": "Customer has shown below-average satisfaction in recent interactions",
                    "action": "Consider reaching out proactively to address concerns"
                })
            elif float(customer.avg_sentiment) > 0.7:
                insights.append({
                    "type": "positive",
                    "category": "satisfaction",
                    "message": "Highly satisfied customer - potential brand advocate",
                    "action": "Consider referral program or loyalty rewards"
                })
        
        # Churn risk insight
        if customer.churn_risk and float(customer.churn_risk) > 0.6:
            insights.append({
                "type": "alert",
                "category": "retention",
                "message": f"High churn risk detected ({float(customer.churn_risk)*100:.0f}%)",
                "action": "Immediate retention outreach recommended"
            })
        
        # VIP potential insight
        if not customer.is_vip and customer.total_spent and float(customer.total_spent) > 1000:
            insights.append({
                "type": "opportunity",
                "category": "vip",
                "message": "Customer spending qualifies for VIP status",
                "action": "Consider upgrading to VIP tier for better retention"
            })
        
        # Engagement insight
        days_since_last = None
        if customer.last_interaction:
            days_since_last = (datetime.utcnow() - customer.last_interaction).days
            
            if days_since_last > 30:
                insights.append({
                    "type": "warning",
                    "category": "engagement",
                    "message": f"Customer hasn't interacted in {days_since_last} days",
                    "action": "Send re-engagement campaign or special offer"
                })
        
        return insights
    
    async def _get_personalized_recommendations(self, customer, ltv: Dict) -> List[str]:
        """Get personalized recommendations for this customer"""
        recommendations = []
        
        # Based on loyalty tier
        tier = customer.loyalty_tier or "standard"
        if tier == "standard" and ltv.get("projected_12_month", 0) > 500:
            recommendations.append("Promote to Silver tier to increase engagement")
        elif tier == "silver" and ltv.get("projected_12_month", 0) > 1500:
            recommendations.append("Qualify for Gold tier benefits")
        
        # Based on preferences
        if customer.preferred_language and customer.preferred_language != "en":
            recommendations.append(f"Greet customer in {customer.preferred_language}")
        
        # Based on churn risk
        if customer.churn_risk and float(customer.churn_risk) > 0.5:
            recommendations.append("Offer exclusive discount to prevent churn")
        
        # Based on spending pattern
        if customer.total_orders and customer.total_orders > 5:
            recommendations.append("Frequent customer - ensure VIP treatment")
        
        return recommendations
    
    async def upsert_customer(
        self,
        db: Session,
        business_id: int,
        phone: str,
        name: str = None,
        email: str = None,
        language: str = None
    ) -> "Customer":
        """Create or update customer record"""
        from app.models.models import Customer
        
        customer = db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.phone == phone
        ).first()
        
        if customer:
            # Update existing
            if name:
                customer.name = name
            if email:
                customer.email = email
            if language:
                customer.preferred_language = language
            customer.updated_at = datetime.utcnow()
        else:
            # Create new
            customer = Customer(
                business_id=business_id,
                phone=phone,
                name=name,
                email=email,
                preferred_language=language or "en",
                customer_since=datetime.utcnow()
            )
            db.add(customer)
        
        db.commit()
        db.refresh(customer)
        
        return customer
    
    async def update_customer_metrics(
        self,
        db: Session,
        customer_id: int
    ) -> Dict:
        """Recalculate all customer metrics"""
        from app.models.models import Customer, CallSession, Order, Appointment
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        
        # Count calls
        calls = db.query(CallSession).filter(
            CallSession.customer_id == customer_id
        ).all()
        
        # Count orders
        orders = db.query(Order).filter(
            Order.customer_id == customer_id
        ).all()
        
        # Count appointments
        appointments = db.query(Appointment).filter(
            Appointment.customer_id == customer_id
        ).all()
        
        # Update counts
        customer.total_calls = len(calls)
        customer.total_orders = len(orders)
        customer.total_appointments = len(appointments)
        
        # Calculate total spent
        total_spent = sum(float(o.total_amount or 0) for o in orders if o.status in ["completed", "confirmed"])
        customer.total_spent = Decimal(str(total_spent))
        
        # Calculate average sentiment
        sentiments = [c.sentiment for c in calls if c.sentiment]
        if sentiments:
            sentiment_scores = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
            avg_sentiment = sum(sentiment_scores.get(s, 0.5) for s in sentiments) / len(sentiments)
            customer.avg_sentiment = Decimal(str(round(avg_sentiment, 2)))
        
        # Calculate average quality score
        quality_scores = [c.quality_score for c in calls if c.quality_score]
        if quality_scores:
            customer.avg_quality_score = Decimal(str(round(
                sum(float(q) for q in quality_scores) / len(quality_scores), 2
            )))
        
        # Update last interaction
        last_call = max([c.started_at for c in calls if c.started_at], default=None)
        last_order = max([o.created_at for o in orders if o.created_at], default=None)
        last_appt = max([a.appointment_time for a in appointments if a.appointment_time], default=None)
        
        dates = [d for d in [last_call, last_order, last_appt] if d]
        if dates:
            customer.last_interaction = max(dates)
        
        # Update loyalty tier
        customer.loyalty_tier = self._calculate_loyalty_tier(
            float(customer.total_spent or 0),
            len(calls) + len(orders) + len(appointments)
        )
        
        # Calculate churn risk
        customer.churn_risk = Decimal(str(await self._calculate_churn_risk(db, customer)))
        
        # Set VIP status
        customer.is_vip = customer.loyalty_tier in ["gold", "platinum"]
        
        db.commit()
        db.refresh(customer)
        
        return {
            "customer_id": customer_id,
            "updated_metrics": {
                "total_calls": customer.total_calls,
                "total_orders": customer.total_orders,
                "total_appointments": customer.total_appointments,
                "total_spent": float(customer.total_spent),
                "loyalty_tier": customer.loyalty_tier,
                "churn_risk": float(customer.churn_risk),
                "is_vip": customer.is_vip
            }
        }
    
    def _calculate_loyalty_tier(self, total_spent: float, total_interactions: int) -> str:
        """Calculate loyalty tier based on spend and interactions"""
        for tier, thresholds in reversed(list(self.LOYALTY_TIERS.items())):
            if total_spent >= thresholds["min_spend"] and total_interactions >= thresholds["min_interactions"]:
                return tier
        return "standard"
    
    async def _calculate_churn_risk(self, db: Session, customer) -> float:
        """Calculate customer churn risk score"""
        from app.models.models import CallSession, Order
        
        risk_score = 0.0
        
        # Time since last interaction
        if customer.last_interaction:
            days_inactive = (datetime.utcnow() - customer.last_interaction).days
            if days_inactive > 60:
                risk_score += 0.3
            elif days_inactive > 30:
                risk_score += 0.15
            elif days_inactive > 14:
                risk_score += 0.05
        
        # Declining sentiment
        if customer.avg_sentiment and float(customer.avg_sentiment) < 0.4:
            risk_score += 0.25
        
        # Low engagement
        if customer.total_calls and customer.total_calls < 2:
            risk_score += 0.1
        
        # Recent complaints (negative sentiment calls)
        if customer.id:
            recent_calls = db.query(CallSession).filter(
                CallSession.customer_id == customer.id,
                CallSession.sentiment == "negative"
            ).count()
            if recent_calls > 0:
                risk_score += min(0.2, recent_calls * 0.1)
        
        return min(1.0, risk_score)
    
    async def get_top_customers(
        self,
        db: Session,
        business_id: int,
        limit: int = 10,
        sort_by: str = "lifetime_value"
    ) -> List[Dict]:
        """Get top customers by various metrics"""
        from app.models.models import Customer
        
        customers = db.query(Customer).filter(
            Customer.business_id == business_id
        ).all()
        
        # Calculate LTV for each and sort
        customer_data = []
        for c in customers:
            ltv = await self._calculate_lifetime_value(db, c)
            customer_data.append({
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "loyalty_tier": c.loyalty_tier,
                "total_spent": float(c.total_spent or 0),
                "lifetime_value": ltv["projected_12_month"],
                "total_orders": c.total_orders,
                "churn_risk": float(c.churn_risk or 0),
                "is_vip": c.is_vip
            })
        
        # Sort
        if sort_by == "lifetime_value":
            customer_data.sort(key=lambda x: x["lifetime_value"], reverse=True)
        elif sort_by == "total_spent":
            customer_data.sort(key=lambda x: x["total_spent"], reverse=True)
        elif sort_by == "total_orders":
            customer_data.sort(key=lambda x: x["total_orders"], reverse=True)
        
        return customer_data[:limit]
    
    async def get_customer_segments(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Segment customers for targeted marketing"""
        from app.models.models import Customer
        
        customers = db.query(Customer).filter(
            Customer.business_id == business_id
        ).all()
        
        segments = {
            "vip": [],
            "at_risk": [],
            "loyal": [],
            "new": [],
            "inactive": []
        }
        
        for c in customers:
            ltv = await self._calculate_lifetime_value(db, c)
            
            if c.is_vip:
                segments["vip"].append({"id": c.id, "name": c.name, "phone": c.phone})
            elif c.churn_risk and float(c.churn_risk) > 0.5:
                segments["at_risk"].append({"id": c.id, "name": c.name, "phone": c.phone, "risk": float(c.churn_risk)})
            elif c.loyalty_tier in ["gold", "silver"]:
                segments["loyal"].append({"id": c.id, "name": c.name, "phone": c.phone})
            elif c.customer_since and (datetime.utcnow() - c.customer_since).days < 30:
                segments["new"].append({"id": c.id, "name": c.name, "phone": c.phone})
            elif c.last_interaction and (datetime.utcnow() - c.last_interaction).days > 30:
                segments["inactive"].append({"id": c.id, "name": c.name, "phone": c.phone, "days_inactive": (datetime.utcnow() - c.last_interaction).days})
        
        return {
            "total_customers": len(customers),
            "segments": {k: {"count": len(v), "customers": v[:10]} for k, v in segments.items()}
        }
    
    async def get_customer_calls(
        self,
        customer_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """Get customer call history"""
        from app.models.models import CallSession
        
        calls = db.query(CallSession).filter(
            CallSession.customer_id == customer_id
        ).order_by(CallSession.started_at.desc()).limit(limit).all()
        
        return [
            {
                "id": c.id,
                "call_date": c.started_at.isoformat() if c.started_at else None,
                "duration": c.duration_seconds,
                "sentiment": c.sentiment,
                "quality_score": float(c.quality_score) if c.quality_score else None,
                "summary": c.summary
            }
            for c in calls
        ]
    
    async def get_customer_appointments(
        self,
        customer_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """Get customer appointments"""
        from app.models.models import Appointment
        
        appointments = db.query(Appointment).filter(
            Appointment.customer_id == customer_id
        ).order_by(Appointment.appointment_time.desc()).limit(limit).all()
        
        return [
            {
                "id": a.id,
                "appointment_time": a.appointment_time.isoformat() if a.appointment_time else None,
                "service": a.service_type,
                "status": a.status,
                "notes": a.notes
            }
            for a in appointments
        ]
    
    async def get_customer_orders(
        self,
        customer_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """Get customer orders"""
        from app.models.models import Order
        
        orders = db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(Order.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": o.id,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "total_amount": float(o.total_amount) if o.total_amount else 0,
                "status": o.status,
                "delivery_method": o.delivery_method
            }
            for o in orders
        ]
    
    async def calculate_lifetime_value(
        self,
        customer_id: int,
        db: Session
    ) -> float:
        """Calculate customer lifetime value"""
        from app.models.models import Customer, Order
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return 0.0
        
        # Sum all completed and confirmed orders
        orders = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.status.in_(["completed", "confirmed"])
        ).all()
        
        ltv = sum(float(o.total_amount or 0) for o in orders)
        return round(ltv, 2)
    
    async def calculate_churn_risk(
        self,
        customer_id: int,
        db: Session
    ) -> float:
        """Calculate customer churn risk score"""
        from app.models.models import Customer
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return 0.5  # Default medium risk
        
        risk_score = 0.0
        
        # Time since last interaction
        if customer.last_interaction:
            days_inactive = (datetime.utcnow() - customer.last_interaction).days
            if days_inactive > 60:
                risk_score += 0.4
            elif days_inactive > 30:
                risk_score += 0.2
            elif days_inactive > 14:
                risk_score += 0.1
        
        # Low satisfaction
        if customer.avg_sentiment and float(customer.avg_sentiment) < 0.4:
            risk_score += 0.3
        
        # Low engagement
        total_interactions = (customer.total_calls or 0) + (customer.total_orders or 0) + (customer.total_appointments or 0)
        if total_interactions < 2:
            risk_score += 0.2
        
        return min(1.0, round(risk_score, 2))
    
    async def calculate_satisfaction_score(
        self,
        customer_id: int,
        db: Session
    ) -> float:
        """Calculate customer satisfaction score"""
        from app.models.models import Customer
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.avg_sentiment:
            return 3.0  # Default neutral
        
        # Convert sentiment (0-1) to score (1-5)
        sentiment = float(customer.avg_sentiment)
        score = 1 + (sentiment * 4)  # Maps 0->1, 1->5
        return round(score, 1)
    
    async def determine_loyalty_tier(
        self,
        customer_id: int,
        db: Session
    ) -> str:
        """Determine customer loyalty tier"""
        from app.models.models import Customer, Order
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return "bronze"
        
        total_spent = float(customer.total_spent or 0)
        total_interactions = (customer.total_calls or 0) + (customer.total_orders or 0)
        
        return self._calculate_loyalty_tier(total_spent, total_interactions)
    
    async def identify_vip(
        self,
        customer,
        db: Session
    ) -> bool:
        """Check if customer qualifies as VIP"""
        # High lifetime value (> $2000)
        if customer.lifetime_value and float(customer.lifetime_value) > 2000:
            return True
        
        # High satisfaction score (> 4.5)
        if customer.satisfaction_score and customer.satisfaction_score > 4.5:
            return True
        
        # Gold or platinum tier
        if customer.loyalty_tier in ["gold", "platinum"]:
            return True
        
        return False
    
    async def segment_customers_by_tier(self, db: Session) -> Dict[str, int]:
        """Segment customers by loyalty tier"""
        from app.models.models import Customer
        
        customers = db.query(Customer).all()
        
        segments = {"platinum": 0, "gold": 0, "silver": 0, "bronze": 0, "standard": 0}
        
        for c in customers:
            tier = c.loyalty_tier or "standard"
            if tier in segments:
                segments[tier] += 1
        
        return segments
    
    async def segment_customers_by_risk(self, db: Session) -> Dict[str, int]:
        """Segment customers by churn risk"""
        from app.models.models import Customer
        
        customers = db.query(Customer).all()
        
        segments = {"low": 0, "medium": 0, "high": 0}
        
        for c in customers:
            risk = float(c.churn_risk or 0.5)
            if risk < 0.3:
                segments["low"] += 1
            elif risk < 0.6:
                segments["medium"] += 1
            else:
                segments["high"] += 1
        
        return segments
    
    async def get_customer_insights(
        self,
        customer_id: int,
        db: Session
    ) -> Dict:
        """Get comprehensive customer insights"""
        from app.models.models import Customer, CallSession, Order
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found"}
        
        calls = db.query(CallSession).filter(
            CallSession.customer_id == customer_id
        ).all()
        
        orders = db.query(Order).filter(
            Order.customer_id == customer_id
        ).all()
        
        ltv = await self._calculate_lifetime_value(customer_id, db)
        
        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "loyalty_tier": customer.loyalty_tier,
                "churn_risk": float(customer.churn_risk or 0),
                "is_vip": customer.is_vip,
                "lifetime_value": ltv,
                "satisfaction_score": await self.calculate_satisfaction_score(customer_id, db)
            },
            "metrics": {
                "total_calls": customer.total_calls,
                "total_orders": customer.total_orders,
                "lifetime_value": ltv,
                "satisfaction_score": await self.calculate_satisfaction_score(customer_id, db)
            },
            "risk": {
                "churn_risk": float(customer.churn_risk or 0)
            },
            "tier": customer.loyalty_tier,
            "is_vip": customer.is_vip
        }


# Singleton instance
customer_360_service = Customer360Service()
