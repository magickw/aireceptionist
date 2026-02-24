"""
Inventory Management Service
Tracks menu item stock levels, handles low stock alerts, and integrates with orders
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from decimal import Decimal

from app.models.models import MenuItem, Order, OrderItem, Business
from app.services.sms_service import sms_service
from app.services.whatsapp_service import whatsapp_service
from app.services.email_service import email_service


class InventoryService:
    """Service for inventory management and stock tracking"""
    
    # Stock status levels
    STOCK_STATUS = {
        "in_stock": 100,        # Above 50%
        "low_stock": 20,        # 20-50%
        "critical": 5,          # 5-20%
        "out_of_stock": 0       # 0-5%
    }
    
    def __init__(self):
        self.sms_service = sms_service
        self.whatsapp_service = whatsapp_service
        self.email_service = email_service
    
    def get_stock_status(self, current_quantity: int, threshold_low: int, threshold_critical: int) -> str:
        """Determine stock status based on quantity and thresholds"""
        if current_quantity == 0:
            return "out_of_stock"
        elif current_quantity <= threshold_critical:
            return "critical"
        elif current_quantity <= threshold_low:
            return "low_stock"
        else:
            return "in_stock"
    
    def get_menu_item_stock(
        self,
        db: Session,
        business_id: int,
        menu_item_id: int
    ) -> Dict[str, Any]:
        """
        Get current stock for a menu item
        
        Note: This requires the menu_items table to have stock columns.
        For now, we calculate from order history.
        """
        # Calculate quantity used in active orders
        used_quantity = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
            and_(
                Order.business_id == business_id,
                OrderItem.menu_item_id == menu_item_id,
                Order.status.in_(["confirmed", "preparing", "ready"]),
                Order.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
            )
        ).scalar() or 0
        
        # Get menu item
        menu_item = db.query(MenuItem).filter(
            and_(
                MenuItem.id == menu_item_id,
                MenuItem.business_id == business_id
            )
        ).first()
        
        if not menu_item:
            return {"success": False, "error": "Menu item not found"}
        
        # Simulate stock based on a baseline (this would be real inventory in production)
        # In production, you'd have a dedicated inventory_items table
        baseline_stock = 100  # Default baseline
        
        current_stock = max(0, baseline_stock - used_quantity)
        
        # Get thresholds from dietary_info (temporary storage) or use defaults
        thresholds = menu_item.dietary_info or {}
        threshold_low = thresholds.get("inventory_threshold_low", 20)
        threshold_critical = thresholds.get("inventory_threshold_critical", 5)
        
        status = self.get_stock_status(current_stock, threshold_low, threshold_critical)
        
        return {
            "success": True,
            "menu_item_id": menu_item_id,
            "menu_item_name": menu_item.name,
            "current_quantity": current_stock,
            "status": status,
            "threshold_low": threshold_low,
            "threshold_critical": threshold_critical,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def get_all_inventory(
        self,
        db: Session,
        business_id: int,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get inventory status for all menu items"""
        menu_items = db.query(MenuItem).filter(
            and_(
                MenuItem.business_id == business_id,
                MenuItem.is_active == True
            )
        ).all()
        
        inventory_list = []
        alert_count = 0
        
        for item in menu_items:
            stock_info = self.get_menu_item_stock(db, business_id, item.id)
            if stock_info["success"]:
                inventory_list.append(stock_info)
                
                if stock_info["status"] in ["low_stock", "critical", "out_of_stock"]:
                    alert_count += 1
        
        # Filter by status if requested
        if status_filter:
            inventory_list = [i for i in inventory_list if i["status"] == status_filter]
        
        return {
            "success": True,
            "business_id": business_id,
            "total_items": len(inventory_list),
            "items": inventory_list,
            "alerts": alert_count,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def check_availability(
        self,
        db: Session,
        business_id: int,
        menu_item_id: int,
        quantity: int
    ) -> Dict[str, Any]:
        """Check if sufficient stock is available for an order"""
        stock_info = self.get_menu_item_stock(db, business_id, menu_item_id)
        
        if not stock_info["success"]:
            return {"success": False, "error": stock_info["error"]}
        
        if stock_info["status"] == "out_of_stock":
            return {
                "success": False,
                "available": False,
                "reason": "Item is out of stock",
                "current_quantity": stock_info["current_quantity"]
            }
        
        if stock_info["current_quantity"] < quantity:
            return {
                "success": False,
                "available": False,
                "reason": f"Only {stock_info['current_quantity']} available",
                "requested_quantity": quantity,
                "current_quantity": stock_info["current_quantity"]
            }
        
        return {
            "success": True,
            "available": True,
            "current_quantity": stock_info["current_quantity"],
            "requested_quantity": quantity,
            "remaining_after_order": stock_info["current_quantity"] - quantity
        }
    
    def check_order_availability(
        self,
        db: Session,
        business_id: int,
        order_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check availability for all items in an order"""
        unavailable_items = []
        all_available = True
        
        for item in order_items:
            menu_item_id = item.get("menu_item_id")
            quantity = item.get("quantity", 1)
            
            availability = self.check_availability(db, business_id, menu_item_id, quantity)
            
            if not availability["available"]:
                all_available = False
                unavailable_items.append({
                    "menu_item_id": menu_item_id,
                    "item_name": item.get("item_name", f"Item {menu_item_id}"),
                    "requested": quantity,
                    "available": availability.get("current_quantity", 0),
                    "reason": availability.get("reason", "Unknown")
                })
        
        return {
            "success": all_available,
            "all_available": all_available,
            "unavailable_items": unavailable_items,
            "total_items": len(order_items),
            "available_items": len(order_items) - len(unavailable_items)
        }
    
    async def send_low_stock_alert(
        self,
        db: Session,
        business_id: int,
        menu_item_id: int,
        alert_type: str = "low_stock"
    ) -> Dict[str, Any]:
        """
        Send alert for low or critical stock levels
        
        Args:
            db: Database session
            business_id: Business ID
            menu_item_id: Menu item ID
            alert_type: Type of alert (low_stock, critical, out_of_stock)
        """
        stock_info = self.get_menu_item_stock(db, business_id, menu_item_id)
        
        if not stock_info["success"]:
            return {"success": False, "error": "Failed to get stock info"}
        
        # Get business contact info
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"success": False, "error": "Business not found"}
        
        # Build alert message
        item_name = stock_info["menu_item_name"]
        current_qty = stock_info["current_quantity"]
        
        if alert_type == "critical":
            title = "🚨 CRITICAL: Stock Alert"
            message = f"CRITICAL: {item_name} is critically low ({current_qty} remaining). Restock immediately!"
        elif alert_type == "out_of_stock":
            title = "⛔ OUT OF STOCK: Alert"
            message = f"OUT OF STOCK: {item_name} is completely out of stock. Cannot accept orders."
        else:
            title = "⚠️ Low Stock: Alert"
            message = f"Low Stock: {item_name} is running low ({current_qty} remaining). Consider restocking."
        
        results = {}
        
        # Send SMS alert
        if business.phone:
            sms_result = await self.sms_service.send_sms(
                to_number=business.phone,
                message=f"{title}\n\n{message}"
            )
            results["sms"] = sms_result
        
        # Send WhatsApp alert
        if business.phone:
            whatsapp_result = await self.whatsapp_service.send_whatsapp_message(
                to_number=business.phone,
                message=f"*{title}*\n\n{message}"
            )
            results["whatsapp"] = whatsapp_result
        
        # Send email alert
        if business.email:
            email_result = await self.email_service.send_email(
                to_email=business.email,
                subject=title,
                body=message
            )
            results["email"] = email_result
        
        return {
            "success": True,
            "alert_type": alert_type,
            "menu_item": item_name,
            "current_quantity": current_qty,
            "notifications_sent": list(results.keys())
        }
    
    async def check_and_send_alerts(
        self,
        db: Session,
        business_id: int
    ) -> Dict[str, Any]:
        """
        Check all inventory and send alerts for items that need attention
        """
        inventory = self.get_all_inventory(db, business_id)
        
        if not inventory["success"]:
            return inventory
        
        alerts_sent = []
        
        for item in inventory["items"]:
            status = item["status"]
            
            if status == "critical":
                result = await self.send_low_stock_alert(
                    db, business_id, item["menu_item_id"], "critical"
                )
                if result["success"]:
                    alerts_sent.append({
                        "item": item["menu_item_name"],
                        "type": "critical",
                        "quantity": item["current_quantity"]
                    })
            
            elif status == "out_of_stock":
                result = await self.send_low_stock_alert(
                    db, business_id, item["menu_item_id"], "out_of_stock"
                )
                if result["success"]:
                    alerts_sent.append({
                        "item": item["menu_item_name"],
                        "type": "out_of_stock",
                        "quantity": item["current_quantity"]
                    })
        
        return {
            "success": True,
            "business_id": business_id,
            "alerts_sent": alerts_sent,
            "total_alerts": len(alerts_sent),
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_inventory_report(
        self,
        db: Session,
        business_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate inventory usage report over a period
        
        Args:
            db: Database session
            business_id: Business ID
            days: Number of days to look back
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all orders in the period
        orders = db.query(Order).filter(
            and_(
                Order.business_id == business_id,
                Order.created_at >= start_date,
                Order.status.in_(["confirmed", "preparing", "ready", "completed"])
            )
        ).all()
        
        # Aggregate usage by menu item
        usage_by_item = {}
        
        for order in orders:
            for item in order.items:
                if item.menu_item_id:
                    menu_item_id = item.menu_item_id
                    item_name = item.item_name
                    
                    if menu_item_id not in usage_by_item:
                        usage_by_item[menu_item_id] = {
                            "menu_item_id": menu_item_id,
                            "menu_item_name": item_name,
                            "total_quantity": 0,
                            "total_orders": 0,
                            "total_revenue": 0
                        }
                    
                    usage_by_item[menu_item_id]["total_quantity"] += item.quantity
                    usage_by_item[menu_item_id]["total_orders"] += 1
                    usage_by_item[menu_item_id]["total_revenue"] += float(item.unit_price * item.quantity)
        
        # Sort by quantity used
        sorted_usage = sorted(
            usage_by_item.values(),
            key=lambda x: x["total_quantity"],
            reverse=True
        )
        
        # Get current inventory for each item
        for usage in sorted_usage:
            stock_info = self.get_menu_item_stock(db, business_id, usage["menu_item_id"])
            if stock_info["success"]:
                usage["current_stock"] = stock_info["current_quantity"]
                usage["stock_status"] = stock_info["status"]
        
        return {
            "success": True,
            "business_id": business_id,
            "period_days": days,
            "total_orders": len(orders),
            "items_reported": len(sorted_usage),
            "items": sorted_usage,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def set_inventory_thresholds(
        self,
        db: Session,
        business_id: int,
        menu_item_id: int,
        threshold_low: int,
        threshold_critical: int
    ) -> Dict[str, Any]:
        """
        Set custom inventory thresholds for a menu item
        
        Note: Stores thresholds in dietary_info field (temporary).
        In production, you'd have dedicated inventory table.
        """
        menu_item = db.query(MenuItem).filter(
            and_(
                MenuItem.id == menu_item_id,
                MenuItem.business_id == business_id
            )
        ).first()
        
        if not menu_item:
            return {"success": False, "error": "Menu item not found"}
        
        # Initialize dietary_info if not present
        if not menu_item.dietary_info:
            menu_item.dietary_info = {}
        
        # Set thresholds
        menu_item.dietary_info.update({
            "inventory_threshold_low": threshold_low,
            "inventory_threshold_critical": threshold_critical,
            "inventory_thresholds_updated": datetime.now(timezone.utc).isoformat()
        })
        
        db.commit()
        db.refresh(menu_item)
        
        return {
            "success": True,
            "menu_item_id": menu_item_id,
            "menu_item_name": menu_item.name,
            "threshold_low": threshold_low,
            "threshold_critical": threshold_critical
        }
    
    def get_fast_moving_items(
        self,
        db: Session,
        business_id: int,
        days: int = 30,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get items with highest usage (fast moving)"""
        report = self.get_inventory_report(db, business_id, days)
        
        if not report["success"]:
            return report
        
        fast_moving = report["items"][:limit]
        
        return {
            "success": True,
            "business_id": business_id,
            "period_days": days,
            "fast_moving_items": fast_moving,
            "total_items": len(fast_moving)
        }
    
    def get_slow_moving_items(
        self,
        db: Session,
        business_id: int,
        days: int = 30,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get items with lowest usage (slow moving)"""
        report = self.get_inventory_report(db, business_id, days)
        
        if not report["success"]:
            return report
        
        slow_moving = report["items"][-limit:] if len(report["items"]) >= limit else report["items"]
        slow_moving.reverse()  # Show least used first
        
        return {
            "success": True,
            "business_id": business_id,
            "period_days": days,
            "slow_moving_items": slow_moving,
            "total_items": len(slow_moving)
        }


# Singleton instance
inventory_service = InventoryService()