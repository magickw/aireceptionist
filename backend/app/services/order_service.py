"""
Order Service with Status Notifications
Handles order management and real-time status updates
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import Order, OrderItem, MenuItem, Business, CallSession
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate
from app.services.sms_service import sms_service
from app.services.whatsapp_service import whatsapp_service
from app.services.email_service import email_service


class OrderService:
    """Service for order management with status notifications"""
    
    # Order status flow
    STATUS_FLOW = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["preparing", "cancelled"],
        "preparing": ["ready", "cancelled"],
        "ready": ["completed", "cancelled"],
        "completed": [],  # Final state
        "cancelled": []   # Final state
    }
    
    # Status descriptions for notifications
    STATUS_MESSAGES = {
        "confirmed": {
            "title": "Order Confirmed",
            "message": "Your order has been confirmed and is being prepared!",
            "voice": "Great news! Your order has been confirmed and we're getting started on it right now."
        },
        "preparing": {
            "title": "Order Preparing",
            "message": "Your order is currently being prepared.",
            "voice": "Your order is being prepared now. We're working hard to get it ready for you!"
        },
        "ready": {
            "title": "Order Ready",
            "message": "Your order is ready for pickup!",
            "voice": "Good news! Your order is ready and waiting for you to pick it up."
        },
        "completed": {
            "title": "Order Completed",
            "message": "Thank you! Your order has been completed.",
            "voice": "Thank you! Your order has been completed. We hope you enjoy it!"
        },
        "cancelled": {
            "title": "Order Cancelled",
            "message": "Your order has been cancelled.",
            "voice": "Your order has been cancelled. We're sorry for any inconvenience."
        }
    }
    
    def __init__(self):
        self.sms_service = sms_service
        self.whatsapp_service = whatsapp_service
        self.email_service = email_service
    
    def validate_status_transition(self, current_status: str, new_status: str) -> bool:
        """Check if a status transition is valid"""
        if current_status not in self.STATUS_FLOW:
            return False
        return new_status in self.STATUS_FLOW[current_status]
    
    def get_order_summary(self, order: Order) -> Dict[str, Any]:
        """Get a human-readable summary of the order"""
        items_summary = []
        for item in order.items:
            item_text = f"{item.quantity}x {item.item_name}"
            if item.notes:
                item_text += f" ({item.notes})"
            items_summary.append(item_text)
        
        return {
            "order_id": order.id,
            "customer_name": order.customer_name,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "items": ", ".join(items_summary),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
            "delivery_method": order.notes  # Using notes field for delivery info
        }
    
    async def create_order(
        self,
        db: Session,
        order_data: OrderCreate,
        business_id: int,
        call_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new order"""
        try:
            # Calculate total
            total_amount = sum(
                item.unit_price * item.quantity 
                for item in order_data.items
            )
            
            # Create order
            order = Order(
                business_id=business_id,
                call_session_id=call_session_id,
                customer_name=order_data.customer_name,
                customer_phone=order_data.customer_phone,
                status="pending",
                total_amount=total_amount,
                notes=order_data.notes
            )
            
            db.add(order)
            db.flush()  # Get the ID before adding items
            
            # Add order items
            for item_data in order_data.items:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item_data.menu_item_id,
                    item_name=item_data.item_name,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    notes=item_data.notes
                )
                db.add(order_item)
            
            db.commit()
            db.refresh(order)
            
            return {
                "success": True,
                "order": order,
                "order_id": order.id,
                "total_amount": float(order.total_amount)
            }
        
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_order_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        """Get an order by ID"""
        return db.query(Order).filter(Order.id == order_id).first()
    
    def get_orders_by_business(
        self,
        db: Session,
        business_id: int,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get orders for a business, optionally filtered by status"""
        query = db.query(Order).filter(Order.business_id == business_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.order_by(Order.created_at.desc()).limit(limit).all()
    
    def get_orders_by_customer(
        self,
        db: Session,
        customer_phone: str,
        business_id: int,
        limit: int = 50
    ) -> List[Order]:
        """Get orders for a customer by phone number"""
        return db.query(Order).filter(
            and_(
                Order.customer_phone == customer_phone,
                Order.business_id == business_id
            )
        ).order_by(Order.created_at.desc()).limit(limit).all()
    
    async def update_order_status(
        self,
        db: Session,
        order_id: int,
        new_status: str,
        notify_customer: bool = True,
        notification_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update order status with optional notifications
        
        Args:
            db: Database session
            order_id: Order ID to update
            new_status: New status (confirmed, preparing, ready, completed, cancelled)
            notify_customer: Whether to send notifications to customer
            notification_channels: List of channels (sms, whatsapp, email, voice)
        
        Returns:
            Result dict with success status and order data
        """
        order = self.get_order_by_id(db, order_id)
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Validate status transition
        if not self.validate_status_transition(order.status, new_status):
            return {
                "success": False,
                "error": f"Invalid status transition from {order.status} to {new_status}"
            }
        
        # Update status
        order.status = new_status
        
        # Update timestamps based on status
        if new_status == "confirmed" and not order.confirmed_at:
            order.confirmed_at = datetime.now(timezone.utc)
        elif new_status == "completed" and not order.completed_at:
            order.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(order)
        
        result = {
            "success": True,
            "order": order,
            "order_id": order.id,
            "status": new_status,
            "previous_status": order.status
        }
        
        # Send notifications if requested
        if notify_customer and order.customer_phone:
            await self._send_status_notifications(
                order=order,
                new_status=new_status,
                channels=notification_channels
            )
        
        return result
    
    async def _send_status_notifications(
        self,
        order: Order,
        new_status: str,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notifications for order status update"""
        if new_status not in self.STATUS_MESSAGES:
            return {"success": False, "error": "No notification template for this status"}
        
        template = self.STATUS_MESSAGES[new_status]
        customer_phone = order.customer_phone
        
        if not customer_phone:
            return {"success": False, "error": "No customer phone to notify"}
        
        # Default channels if not specified
        if not channels:
            channels = ["sms"]
        
        results = {}
        order_summary = self.get_order_summary(order)
        
        # SMS notification
        if "sms" in channels:
            message = f"{template['title']}: {template['message']} Order #{order.id}"
            sms_result = await self.sms_service.send_sms(
                to_number=customer_phone,
                message=message
            )
            results["sms"] = sms_result
        
        # WhatsApp notification
        if "whatsapp" in channels:
            whatsapp_message = f"*{template['title']}*\n\n{template['message']}\n\nOrder #{order.id}\nTotal: ${order.total_amount:.2f}"
            whatsapp_result = await self.whatsapp_service.send_whatsapp_message(
                to_number=customer_phone,
                message=whatsapp_message
            )
            results["whatsapp"] = whatsapp_result
        
        # Email notification (if customer has email)
        if "email" in channels:
            # Try to get customer email from order notes or database
            customer_email = None
            # You could add customer_email field to Order model for this
            # For now, skip email if not available
            
            if customer_email:
                email_result = await self.email_service.send_email(
                    to_email=customer_email,
                    subject=template["title"],
                    body=f"{template['message']}\n\nOrder Details:\n{order_summary['items']}\nTotal: ${order.total_amount:.2f}"
                )
                results["email"] = email_result
        
        # Voice notification (outbound call)
        if "voice" in channels:
            voice_result = await self._send_voice_notification(
                order=order,
                message=template["voice"]
            )
            results["voice"] = voice_result
        
        return {
            "success": True,
            "notifications_sent": list(results.keys()),
            "details": results
        }
    
    async def _send_voice_notification(
        self,
        order: Order,
        message: str
    ) -> Dict[str, Any]:
        """Send a voice notification using Polly TTS"""
        try:
            from app.services.nova_sonic import nova_sonic
            
            # Generate TTS audio
            audio_result = await nova_sonic.text_to_speech(
                text=message,
                voice_id="Ruth"  # Natural female voice
            )
            
            if not audio_result.get("success"):
                return {"success": False, "error": "Failed to generate voice"}
            
            # For now, return success - actual outbound call would need
            # integration with Twilio Voice or similar service
            # This is a placeholder for the full implementation
            
            return {
                "success": True,
                "message": "Voice notification generated (outbound call pending)",
                "audio_url": audio_result.get("audio_url")
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cancel_order(
        self,
        db: Session,
        order_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an order with notification"""
        result = await self.update_order_status(
            db=db,
            order_id=order_id,
            new_status="cancelled",
            notify_customer=True,
            notification_channels=["sms", "whatsapp"]
        )
        
        if result["success"]:
            # Add cancellation reason to notes
            order = result["order"]
            if reason:
                if order.notes:
                    order.notes += f"\nCancelled: {reason}"
                else:
                    order.notes = f"Cancelled: {reason}"
                db.commit()
        
        return result
    
    def get_order_status_history(self, db: Session, order_id: int) -> Dict[str, Any]:
        """Get the status history of an order"""
        order = self.get_order_by_id(db, order_id)
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        history = []
        
        # Created
        if order.created_at:
            history.append({
                "status": "created",
                "timestamp": order.created_at.isoformat()
            })
        
        # Confirmed
        if order.confirmed_at:
            history.append({
                "status": "confirmed",
                "timestamp": order.confirmed_at.isoformat()
            })
        
        # Completed
        if order.completed_at:
            history.append({
                "status": "completed",
                "timestamp": order.completed_at.isoformat()
            })
        
        return {
            "success": True,
            "order_id": order_id,
            "current_status": order.status,
            "history": history
        }
    
    def get_active_orders(self, db: Session, business_id: int) -> List[Order]:
        """Get all active (not completed/cancelled) orders for a business"""
        return db.query(Order).filter(
            and_(
                Order.business_id == business_id,
                Order.status.in_(["pending", "confirmed", "preparing", "ready"])
            )
        ).order_by(Order.created_at.asc()).all()
    
    def get_order_statistics(
        self,
        db: Session,
        business_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get order statistics for a business"""
        query = db.query(Order).filter(Order.business_id == business_id)
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        
        orders = query.all()
        
        total_orders = len(orders)
        total_revenue = sum(float(order.total_amount) for order in orders)
        
        # Count by status
        status_counts = {}
        for status in self.STATUS_FLOW.keys():
            status_counts[status] = sum(1 for o in orders if o.status == status)
        
        # Calculate average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            "success": True,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": avg_order_value,
            "status_breakdown": status_counts,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }


# Singleton instance
order_service = OrderService()