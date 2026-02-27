from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class OrderItemBase(BaseModel):
    menu_item_id: Optional[int] = None
    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(1, ge=1, le=9999)
    unit_price: float = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=1000)

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
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=20)
    status: str = Field("pending", pattern=r"^(pending|confirmed|preparing|ready|completed|cancelled)$")
    delivery_method: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
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
    delivery_method: Optional[str] = None
    delivery_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
