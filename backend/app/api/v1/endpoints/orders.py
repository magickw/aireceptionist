"""
Order API endpoints for managing customer orders
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.models import User, Business, Order, OrderItem, MenuItem

router = APIRouter()


# Pydantic schemas
class OrderItemCreate(BaseModel):
    menu_item_id: Optional[int] = None
    item_name: str
    quantity: int = 1
    unit_price: float
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: Optional[int]
    item_name: str
    quantity: int
    unit_price: Decimal
    notes: Optional[str]

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    call_session_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[OrderItemCreate]
    notes: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    business_id: int
    call_session_id: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    status: str
    total_amount: Decimal
    notes: Optional[str]
    confirmed_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    business_id: int,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[Order]:
    """Get all orders for a business"""
    query = db.query(Order).filter(Order.business_id == business_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Order:
    """Create a new order"""
    # Verify business exists
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Calculate total
    total = Decimal("0.00")
    for item in order.items:
        total += Decimal(str(item.unit_price)) * item.quantity
    
    # Create order
    db_order = Order(
        business_id=business_id,
        call_session_id=order.call_session_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        status="pending",
        total_amount=total,
        notes=order.notes,
    )
    db.add(db_order)
    db.flush()  # Get the order ID
    
    # Create order items
    for item in order.items:
        db_item = OrderItem(
            order_id=db_order.id,
            menu_item_id=item.menu_item_id,
            item_name=item.item_name,
            quantity=item.quantity,
            unit_price=Decimal(str(item.unit_price)),
            notes=item.notes,
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Order:
    """Get a specific order"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Order:
    """Update an order (status, customer info, notes)"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = order_update.model_dump(exclude_unset=True)
    
    # Handle status changes
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == "confirmed" and order.status == "pending":
            order.confirmed_at = datetime.utcnow()
        elif new_status == "completed" and order.status in ["confirmed", "preparing", "ready"]:
            order.completed_at = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/confirm", response_model=OrderResponse)
def confirm_order(
    order_id: int,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Order:
    """Confirm a pending order"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot confirm order with status '{order.status}'")
    
    order.status = "confirmed"
    order.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Order:
    """Cancel an order"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order with status '{order.status}'")
    
    order.status = "cancelled"
    
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    business_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """Delete an order (only if cancelled)"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "cancelled":
        raise HTTPException(status_code=400, detail="Can only delete cancelled orders")
    
    db.delete(order)
    db.commit()
    
    return {"status": "deleted"}
