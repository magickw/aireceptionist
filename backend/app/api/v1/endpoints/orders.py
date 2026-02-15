from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.models import Order, OrderItem, User
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderItemResponse

router = APIRouter()

@router.get("/", response_model=List[OrderResponse])
def read_orders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve orders for the current user's business.
    """
    # Assuming a user can only see orders for their own business
    # In a more complex scenario, you might filter by business_id based on user roles
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not own any businesses.",
        )
    
    business_id = current_user.businesses[0].id # Get the first business owned by the user

    orders = db.query(Order).filter(Order.business_id == business_id).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def read_order_by_id(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific order by ID for the current user's business.
    """
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not own any businesses.",
        )
    business_id = current_user.businesses[0].id

    order = db.query(Order).filter(Order.id == order_id, Order.business_id == business_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: OrderCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new order for the current user's business.
    """
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not own any businesses.",
        )
    business_id = current_user.businesses[0].id

    # Validate menu items and calculate total amount
    total_amount = 0.0
    order_items_list = []
    for item_data in order_in.items:
        # Here you would typically fetch the menu item from the DB
        # to get its current price and ensure it exists.
        # For simplicity, we'll use the price provided in the OrderCreate schema.
        unit_price = item_data.unit_price if item_data.unit_price is not None else 0.0
        total_amount += unit_price * item_data.quantity
        order_items_list.append(OrderItem(
            menu_item_id=item_data.menu_item_id,
            item_name=item_data.item_name,
            quantity=item_data.quantity,
            unit_price=unit_price,
            notes=item_data.notes
        ))

    db_order = Order(
        business_id=business_id,
        customer_name=order_in.customer_name,
        customer_phone=order_in.customer_phone,
        total_amount=total_amount,
        status=order_in.status,
        notes=order_in.notes,
        call_session_id=order_in.call_session_id # Associate with call session if available
    )
    db.add(db_order)
    db.flush() # Flush to get db_order.id for order_items

    for order_item in order_items_list:
        order_item.order_id = db_order.id
        db.add(order_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: OrderUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an existing order.
    """
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not own any businesses.",
        )
    business_id = current_user.businesses[0].id

    order = db.query(Order).filter(Order.id == order_id, Order.business_id == business_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = order_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(order, field, update_data[field])

    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}")
def delete_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an order.
    """
    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not own any businesses.",
        )
    business_id = current_user.businesses[0].id

    order = db.query(Order).filter(Order.id == order_id, Order.business_id == business_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return None
