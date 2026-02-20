from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class OrderItemBase(BaseModel):
    menu_item_id: Optional[int] = None
    item_name: str
    quantity: int = 1
    unit_price: float
    notes: Optional[str] = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None
    call_session_id: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(OrderBase):
    items: Optional[List[OrderItemUpdate]] = None
    total_amount: Optional[float] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class OrderResponse(OrderBase):
    id: int
    business_id: int
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True