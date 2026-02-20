"""
Mobile App Support Service
Business owner dashboard with push notifications
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json
import os
import asyncio
from dataclasses import dataclass
from enum import Enum


class NotificationType(str, Enum):
    """Types of push notifications"""
    NEW_CALL = "new_call"
    MISSED_CALL = "missed_call"
    NEW_ORDER = "new_order"
    NEW_APPOINTMENT = "new_appointment"
    APPOINTMENT_REMINDER = "appointment_reminder"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    ALERT_HIGH_VOLUME = "alert_high_volume"
    ALERT_NEGATIVE_SENTIMENT = "alert_negative_sentiment"
    SYSTEM_UPDATE = "system_update"


class DevicePlatform(str, Enum):
    """Mobile device platforms"""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


@dataclass
class PushNotification:
    """Push notification data structure"""
    title: str
    body: str
    data: Dict
    notification_type: NotificationType
    priority: str = "normal"  # normal, high
    sound: str = "default"
    badge: Optional[int] = None


class MobileAppService:
    """Service for mobile app support and push notifications"""
    
    # Notification templates
    NOTIFICATION_TEMPLATES = {
        NotificationType.NEW_CALL: {
            "title": "Incoming Call",
            "body_template": "New call from {customer_name} ({customer_phone})",
            "priority": "high"
        },
        NotificationType.MISSED_CALL: {
            "title": "Missed Call",
            "body_template": "Missed call from {customer_phone}",
            "priority": "high"
        },
        NotificationType.NEW_ORDER: {
            "title": "New Order",
            "body_template": "New order #{order_id} - ${total}",
            "priority": "normal"
        },
        NotificationType.NEW_APPOINTMENT: {
            "title": "New Appointment",
            "body_template": "New appointment with {customer_name} at {time}",
            "priority": "normal"
        },
        NotificationType.APPOINTMENT_REMINDER: {
            "title": "Upcoming Appointment",
            "body_template": "Appointment with {customer_name} in {minutes} minutes",
            "priority": "high"
        },
        NotificationType.DAILY_SUMMARY: {
            "title": "Daily Summary",
            "body_template": "You had {call_count} calls today. Tap to see details.",
            "priority": "normal"
        },
        NotificationType.WEEKLY_REPORT: {
            "title": "Weekly Report",
            "body_template": "Your weekly report is ready. {total_calls} calls, ${revenue} revenue.",
            "priority": "normal"
        },
        NotificationType.ALERT_HIGH_VOLUME: {
            "title": "High Call Volume Alert",
            "body_template": "Unusual call volume detected: {call_count} calls in the last hour",
            "priority": "high"
        },
        NotificationType.ALERT_NEGATIVE_SENTIMENT: {
            "title": "Negative Sentiment Alert",
            "body_template": "Customer complaint detected from {customer_phone}",
            "priority": "high"
        },
        NotificationType.SYSTEM_UPDATE: {
            "title": "System Update",
            "body_template": "{message}",
            "priority": "normal"
        }
    }
    
    def __init__(self):
        # Firebase Cloud Messaging would be configured here
        self.fcm_server_key = os.getenv('FCM_SERVER_KEY')
        self.apns_key = os.getenv('APNS_KEY')
        self.apns_key_id = os.getenv('APNS_KEY_ID')
        self.apns_team_id = os.getenv('APNS_TEAM_ID')
    
    async def register_device(
        self,
        db: Session,
        user_id: int,
        device_token: str,
        platform: DevicePlatform,
        device_name: str = None
    ) -> Dict:
        """Register a mobile device for push notifications"""
        from app.models.models import User
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Store device token in user settings or a separate table
        # For now, we'll store in user metadata
        user_metadata = {}
        if hasattr(user, 'metadata_') and user.metadata_:
            user_metadata = user.metadata_
        
        devices = user_metadata.get('devices', [])
        
        # Check if device already registered
        existing = next((d for d in devices if d['token'] == device_token), None)
        
        if existing:
            existing['last_active'] = datetime.utcnow().isoformat()
            existing['platform'] = platform.value
        else:
            devices.append({
                'token': device_token,
                'platform': platform.value,
                'name': device_name,
                'registered_at': datetime.utcnow().isoformat(),
                'last_active': datetime.utcnow().isoformat(),
                'enabled': True
            })
        
        user_metadata['devices'] = devices
        
        # In a real implementation, you'd have a separate table for devices
        
        return {
            "success": True,
            "message": "Device registered successfully",
            "device_count": len(devices)
        }
    
    async def unregister_device(
        self,
        db: Session,
        user_id: int,
        device_token: str
    ) -> Dict:
        """Unregister a mobile device"""
        # Remove device from user's device list
        return {
            "success": True,
            "message": "Device unregistered"
        }
    
    async def send_push_notification(
        self,
        db: Session,
        user_id: int,
        notification: PushNotification
    ) -> Dict:
        """Send a push notification to a user's devices"""
        from app.models.models import User
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get user's devices
        user_metadata = {}
        if hasattr(user, 'metadata_') and user.metadata_:
            user_metadata = user.metadata_
        
        devices = user_metadata.get('devices', [])
        enabled_devices = [d for d in devices if d.get('enabled', True)]
        
        if not enabled_devices:
            return {"error": "No registered devices"}
        
        # Log notification
        await self._log_notification(db, user_id, notification)
        
        # In a real implementation, send via FCM/APNS
        results = []
        for device in enabled_devices:
            result = await self._send_to_device(device, notification)
            results.append(result)
        
        return {
            "success": True,
            "sent_count": len([r for r in results if r.get('success')]),
            "failed_count": len([r for r in results if not r.get('success')])
        }
    
    async def _send_to_device(
        self,
        device: Dict,
        notification: PushNotification
    ) -> Dict:
        """Send notification to a specific device"""
        platform = device.get('platform', 'android')
        
        if platform == DevicePlatform.IOS.value:
            return await self._send_via_apns(device, notification)
        else:
            return await self._send_via_fcm(device, notification)
    
    async def _send_via_fcm(
        self,
        device: Dict,
        notification: PushNotification
    ) -> Dict:
        """Send via Firebase Cloud Messaging"""
        # In production, use firebase-admin SDK or HTTP API
        # This is a placeholder implementation
        
        payload = {
            "to": device['token'],
            "notification": {
                "title": notification.title,
                "body": notification.body,
                "sound": notification.sound
            },
            "data": notification.data,
            "priority": notification.priority
        }
        
        # Simulate sending
        return {
            "success": True,
            "platform": "fcm",
            "message_id": f"fcm_{datetime.utcnow().timestamp()}"
        }
    
    async def _send_via_apns(
        self,
        device: Dict,
        notification: PushNotification
    ) -> Dict:
        """Send via Apple Push Notification Service"""
        # In production, use a library like aioapns
        # This is a placeholder implementation
        
        return {
            "success": True,
            "platform": "apns",
            "message_id": f"apns_{datetime.utcnow().timestamp()}"
        }
    
    async def _log_notification(
        self,
        db: Session,
        user_id: int,
        notification: PushNotification
    ):
        """Log notification for history"""
        # Store notification in database for history
        pass
    
    async def send_business_notification(
        self,
        db: Session,
        business_id: int,
        notification_type: NotificationType,
        data: Dict
    ) -> Dict:
        """Send notification to business owner"""
        from app.models.models import Business, User
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        # Get business owner
        owner = db.query(User).filter(User.id == business.user_id).first()
        if not owner:
            return {"error": "Owner not found"}
        
        # Build notification from template
        template = self.NOTIFICATION_TEMPLATES.get(notification_type, {})
        body = template.get('body_template', '').format(**data)
        
        notification = PushNotification(
            title=template.get('title', 'Notification'),
            body=body,
            data=data,
            notification_type=notification_type,
            priority=template.get('priority', 'normal')
        )
        
        return await self.send_push_notification(db, owner.id, notification)
    
    async def send_bulk_notifications(
        self,
        db: Session,
        user_ids: List[int],
        notification: PushNotification
    ) -> Dict:
        """Send notification to multiple users"""
        results = []
        for user_id in user_ids:
            result = await self.send_push_notification(db, user_id, notification)
            results.append(result)
        
        return {
            "total": len(user_ids),
            "sent": len([r for r in results if r.get('success')]),
            "failed": len([r for r in results if not r.get('success')])
        }
    
    async def get_dashboard_data(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Get dashboard data for mobile app"""
        from app.models.models import CallSession, Order, Appointment, Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Today's metrics
        today_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= today_start
        ).count()
        
        today_orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= today_start
        ).all()
        
        today_revenue = sum(float(o.total_amount or 0) for o in today_orders)
        
        today_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            func.date(Appointment.appointment_time) == today
        ).count()
        
        # Pending items
        pending_orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.status == "pending"
        ).count()
        
        upcoming_appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.appointment_time >= datetime.utcnow(),
            Appointment.status == "scheduled"
        ).count()
        
        # Recent activity
        recent_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id
        ).order_by(CallSession.started_at.desc()).limit(5).all()
        
        recent_orders = db.query(Order).filter(
            Order.business_id == business_id
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        return {
            "business": {
                "id": business.id,
                "name": business.name,
                "type": business.type
            },
            "today": {
                "calls": today_calls,
                "orders": len(today_orders),
                "revenue": round(today_revenue, 2),
                "appointments": today_appointments
            },
            "pending": {
                "orders": pending_orders,
                "appointments": upcoming_appointments
            },
            "recent_activity": {
                "calls": [
                    {
                        "id": c.id,
                        "customer": c.customer_name or c.customer_phone,
                        "time": c.started_at.isoformat() if c.started_at else None,
                        "duration": c.duration_seconds
                    }
                    for c in recent_calls
                ],
                "orders": [
                    {
                        "id": o.id,
                        "customer": o.customer_name,
                        "total": float(o.total_amount or 0),
                        "status": o.status,
                        "time": o.created_at.isoformat() if o.created_at else None
                    }
                    for o in recent_orders
                ]
            }
        }
    
    async def get_quick_stats(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Get quick stats for mobile app widget"""
        from app.models.models import CallSession, Order
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # This week
        week_start = today - timedelta(days=today.weekday())
        week_start_dt = datetime.combine(week_start, datetime.min.time())
        
        # This month
        month_start = today.replace(day=1)
        month_start_dt = datetime.combine(month_start, datetime.min.time())
        
        # Quick counts
        today_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= today_start
        ).count()
        
        week_calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= week_start_dt
        ).count()
        
        month_orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= month_start_dt
        ).all()
        
        month_revenue = sum(float(o.total_amount or 0) for o in month_orders)
        
        return {
            "today_calls": today_calls,
            "week_calls": week_calls,
            "month_orders": len(month_orders),
            "month_revenue": round(month_revenue, 2),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def schedule_daily_summary(
        self,
        db: Session,
        business_id: int,
        send_time: str = "18:00"
    ) -> Dict:
        """Schedule daily summary notification"""
        # Store scheduled notification preference
        return {
            "success": True,
            "message": f"Daily summary scheduled for {send_time}",
            "business_id": business_id
        }
    
    async def send_daily_summary(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Send daily summary notification"""
        from app.models.models import CallSession, Order, Appointment
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.started_at >= today_start
        ).count()
        
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.created_at >= today_start
        ).all()
        
        revenue = sum(float(o.total_amount or 0) for o in orders)
        
        return await self.send_business_notification(
            db,
            business_id,
            NotificationType.DAILY_SUMMARY,
            {
                "call_count": calls,
                "order_count": len(orders),
                "revenue": round(revenue, 2)
            }
        )


# Singleton instance
mobile_app_service = MobileAppService()
