"""
Revenue Analytics Service
Provides conversion rates, upsell metrics, and revenue tracking
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


class RevenueAnalyticsService:
    """Service for revenue analytics and conversion tracking"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
    
    async def get_revenue_dashboard(
        self,
        db: Session,
        business_id: int,
        days: int = 30
    ) -> Dict:
        """Get comprehensive revenue dashboard metrics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all metrics in parallel
        revenue_metrics = await self._get_revenue_metrics(db, business_id, start_date)
        conversion_metrics = await self._get_conversion_metrics(db, business_id, start_date)
        upsell_metrics = await self._get_upsell_metrics(db, business_id, start_date)
        call_roi = await self._get_call_roi(db, business_id, start_date)
        
        return {
            "period_days": days,
            "revenue": revenue_metrics,
            "conversions": conversion_metrics,
            "upsells": upsell_metrics,
            "call_roi": call_roi,
            "summary": self._generate_revenue_summary(
                revenue_metrics, conversion_metrics, upsell_metrics
            )
        }
    
    async def _get_revenue_metrics(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> Dict:
        """Get revenue-related metrics"""
        from app.models.models import Order, Appointment, CallSession
        
        # Total revenue from orders
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= start_date,
            Order.status.in_(["completed", "confirmed", "ready"])
        ).all()
        
        total_order_revenue = sum(float(o.total_amount or 0) for o in orders)
        
        # Revenue by day
        daily_revenue = {}
        for order in orders:
            date_key = order.created_at.strftime('%Y-%m-%d')
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + float(order.total_amount or 0)
        
        # Average order value
        avg_order_value = total_order_revenue / len(orders) if orders else 0
        
        # Completed appointments (potential revenue)
        completed_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.appointment_time >= start_date,
            Appointment.status == "completed"
        ).count()
        
        # Revenue trend (compare to previous period)
        prev_start = start_date - timedelta(days=len(daily_revenue) if daily_revenue else 30)
        prev_orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= prev_start,
            Order.created_at < start_date,
            Order.status.in_(["completed", "confirmed", "ready"])
        ).all()
        
        prev_revenue = sum(float(o.total_amount or 0) for o in prev_orders)
        revenue_change = ((total_order_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        return {
            "total_revenue": round(total_order_revenue, 2),
            "total_orders": len(orders),
            "average_order_value": round(avg_order_value, 2),
            "completed_appointments": completed_appointments,
            "daily_revenue": daily_revenue,
            "revenue_trend": {
                "change_percent": round(revenue_change, 1),
                "trend": "up" if revenue_change > 5 else "down" if revenue_change < -5 else "stable"
            }
        }
    
    async def _get_conversion_metrics(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> Dict:
        """Get conversion funnel metrics"""
        from app.models.models import CallSession, Order, Appointment
        
        # Total calls
        total_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).count()
        
        # Calls that resulted in orders
        calls_with_orders = db.query(CallSession).join(Order).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).distinct().count()
        
        # Calls that resulted in appointments
        calls_with_appointments = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.messages.any()  # Has messages
        ).count()  # Simplified - would need appointment link
        
        # Abandoned calls
        abandoned_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.status == "abandoned"
        ).count()
        
        # Calls requiring transfer
        transferred_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            CallSession.status == "transferred"
        ).count()
        
        # Calculate conversion rates
        booking_conversion = (calls_with_orders + calls_with_appointments) / total_calls * 100 if total_calls > 0 else 0
        
        # By intent type
        intent_conversions = await self._get_conversions_by_intent(db, business_id, start_date)
        
        return {
            "total_calls": total_calls,
            "calls_converted": calls_with_orders + calls_with_appointments,
            "conversion_rate": round(booking_conversion, 1),
            "abandoned_calls": abandoned_calls,
            "abandonment_rate": round(abandoned_calls / total_calls * 100, 1) if total_calls > 0 else 0,
            "transfer_rate": round(transferred_calls / total_calls * 100, 1) if total_calls > 0 else 0,
            "by_intent": intent_conversions
        }
    
    async def _get_conversions_by_intent(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> Dict:
        """Get conversion rates broken down by intent"""
        from app.models.models import CallSession, ConversationMessage
        
        # Get intents from messages
        messages = db.query(ConversationMessage).join(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date,
            ConversationMessage.intent.isnot(None)
        ).all()
        
        intent_counts = {}
        for msg in messages:
            intent = msg.intent
            if intent:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return intent_counts
    
    async def _get_upsell_metrics(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> Dict:
        """Get upsell and cross-sell metrics"""
        from app.models.models import Order, OrderItem, MenuItem
        
        # Get all orders with their items
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= start_date
        ).all()
        
        # Calculate upsell metrics
        total_items = 0
        multi_item_orders = 0
        premium_items = 0
        
        for order in orders:
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            total_items += len(items)
            
            if len(items) > 1:
                multi_item_orders += 1
            
            # Check for premium items (higher priced)
            for item in items:
                if float(item.unit_price or 0) > 20:  # Threshold for "premium"
                    premium_items += 1
        
        # Upsell rate = orders with multiple items / total orders
        upsell_rate = multi_item_orders / len(orders) * 100 if orders else 0
        
        # Average items per order
        avg_items = total_items / len(orders) if orders else 0
        
        # Get popular add-ons
        popular_addons = await self._get_popular_addons(db, business_id, start_date)
        
        return {
            "upsell_rate": round(upsell_rate, 1),
            "average_items_per_order": round(avg_items, 2),
            "multi_item_orders": multi_item_orders,
            "premium_item_orders": premium_items,
            "popular_addons": popular_addons,
            "upsell_opportunities_missed": await self._identify_missed_upsells(db, business_id, start_date)
        }
    
    async def _get_popular_addons(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> List[Dict]:
        """Get most popular add-on items"""
        from app.models.models import Order, OrderItem
        
        # Get items from multi-item orders
        addon_counts = {}
        
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= start_date
        ).all()
        
        for order in orders:
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            if len(items) > 1:
                # Second item and beyond are considered "add-ons"
                for item in items[1:]:
                    name = item.item_name
                    if name:
                        addon_counts[name] = addon_counts.get(name, 0) + 1
        
        # Sort by count
        sorted_addons = sorted(addon_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [{"item": name, "count": count} for name, count in sorted_addons]
    
    async def _identify_missed_upsells(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> int:
        """Identify orders where upsell could have been suggested"""
        from app.models.models import Order, OrderItem
        
        # Single item orders are potential missed upsells
        single_item_orders = 0
        
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= start_date
        ).all()
        
        for order in orders:
            item_count = db.query(OrderItem).filter(OrderItem.order_id == order.id).count()
            if item_count == 1:
                single_item_orders += 1
        
        return single_item_orders
    
    async def _get_call_roi(
        self,
        db: Session,
        business_id: int,
        start_date: datetime
    ) -> Dict:
        """Calculate ROI from AI calls"""
        from app.models.models import CallSession, Order
        
        # Get all calls
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= start_date
        ).all()
        
        # Get revenue from calls
        total_revenue = 0
        calls_with_revenue = 0
        
        for call in calls:
            orders = db.query(Order).filter(
                Order.call_session_id == call.id,
                Order.status.in_(["completed", "confirmed", "ready"])
            ).all()
            
            call_revenue = sum(float(o.total_amount or 0) for o in orders)
            if call_revenue > 0:
                calls_with_revenue += 1
                total_revenue += call_revenue
        
        # Calculate costs (estimated AWS costs)
        total_duration = sum(c.duration_seconds or 0 for c in calls)
        # Approximate cost: $0.008 per minute for Nova Sonic
        estimated_cost = (total_duration / 60) * 0.008
        
        # Calculate ROI
        roi = ((total_revenue - estimated_cost) / estimated_cost * 100) if estimated_cost > 0 else 0
        
        return {
            "total_calls": len(calls),
            "revenue_generating_calls": calls_with_revenue,
            "total_revenue": round(total_revenue, 2),
            "estimated_cost": round(estimated_cost, 2),
            "roi_percent": round(roi, 1),
            "revenue_per_call": round(total_revenue / len(calls), 2) if calls else 0,
            "average_call_duration_seconds": total_duration / len(calls) if calls else 0
        }
    
    def _generate_revenue_summary(
        self,
        revenue: Dict,
        conversions: Dict,
        upsells: Dict
    ) -> Dict:
        """Generate a summary with key insights"""
        insights = []
        
        # Revenue insights
        if revenue.get("revenue_trend", {}).get("trend") == "up":
            insights.append(f"Revenue is up {revenue['revenue_trend']['change_percent']}% compared to previous period")
        elif revenue.get("revenue_trend", {}).get("trend") == "down":
            insights.append(f"Revenue is down {abs(revenue['revenue_trend']['change_percent'])}% - consider promotional offers")
        
        # Conversion insights
        if conversions.get("conversion_rate", 0) > 30:
            insights.append("Excellent conversion rate! The AI is effectively handling customer requests")
        elif conversions.get("conversion_rate", 0) < 15:
            insights.append("Conversion rate is below average - review call handling and scripts")
        
        if conversions.get("abandonment_rate", 0) > 20:
            insights.append("High abandonment rate detected - check for system issues or improve greeting")
        
        # Upsell insights
        if upsells.get("upsell_rate", 0) > 40:
            insights.append("Great upsell rate! Customers are adding items to their orders")
        elif upsells.get("missed_upsells", 0) > 50:
            insights.append(f"{upsells['missed_upsells']} orders missed upsell opportunities - train AI to suggest add-ons")
        
        return {
            "key_metrics": {
                "total_revenue": revenue.get("total_revenue"),
                "conversion_rate": conversions.get("conversion_rate"),
                "upsell_rate": upsells.get("upsell_rate"),
                "revenue_per_call": revenue.get("total_revenue", 0) / max(1, conversions.get("total_calls", 1))
            },
            "insights": insights,
            "recommendations": self._generate_recommendations(revenue, conversions, upsells)
        }
    
    def _generate_recommendations(self, revenue: Dict, conversions: Dict, upsells: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Conversion recommendations
        if conversions.get("transfer_rate", 0) > 15:
            recommendations.append("Reduce transfer rate by improving AI training for common scenarios")
        
        if conversions.get("abandonment_rate", 0) > 15:
            recommendations.append("Investigate call abandonment - check wait times and greeting effectiveness")
        
        # Upsell recommendations
        if upsells.get("upsell_rate", 0) < 30:
            recommendations.append("Implement upsell prompts for popular add-on items")
        
        if upsells.get("missed_upsells", 0) > 30:
            recommendations.append("Train AI to suggest complementary items during ordering")
        
        # Revenue recommendations
        if revenue.get("average_order_value", 0) < 25:
            recommendations.append("Focus on increasing order value through combo deals or specials")
        
        return recommendations
    
    async def get_revenue_forecast(
        self,
        db: Session,
        business_id: int,
        forecast_days: int = 7
    ) -> Dict:
        """Forecast revenue for upcoming days"""
        from app.models.models import Order
        
        # Get historical data
        historical_days = 30
        start_date = datetime.utcnow() - timedelta(days=historical_days)
        
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= start_date,
            Order.status.in_(["completed", "confirmed", "ready"])
        ).all()
        
        # Group by day
        daily_revenue = {}
        for order in orders:
            date_key = order.created_at.strftime('%Y-%m-%d')
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + float(order.total_amount or 0)
        
        # Calculate trend and forecast
        if len(daily_revenue) < 7:
            return {"error": "Insufficient data for forecast"}
        
        revenues = list(daily_revenue.values())
        avg_revenue = sum(revenues) / len(revenues)
        
        # Simple linear trend forecast
        recent_avg = sum(revenues[-7:]) / 7
        trend = (recent_avg - avg_revenue) / avg_revenue if avg_revenue > 0 else 0
        
        forecast = []
        for i in range(forecast_days):
            forecast_date = (datetime.utcnow() + timedelta(days=i+1)).strftime('%Y-%m-%d')
            predicted = recent_avg * (1 + trend * i / 7)
            forecast.append({
                "date": forecast_date,
                "predicted_revenue": round(max(0, predicted), 2)
            })
        
        return {
            "forecast_period_days": forecast_days,
            "historical_average_daily": round(avg_revenue, 2),
            "recent_average_daily": round(recent_avg, 2),
            "trend": "up" if trend > 0.05 else "down" if trend < -0.05 else "stable",
            "forecast": forecast
        }


# Singleton instance
revenue_analytics_service = RevenueAnalyticsService()
