from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.models import Order, User
from app.services.payment_service import payment_service

router = APIRouter()


class PaymentIntentRequest(BaseModel):
    order_id: int
    currency: str = "usd"


class CheckoutRequest(BaseModel):
    order_id: int
    success_url: str
    cancel_url: str


@router.get("/status")
def payment_status(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Check if Stripe is configured."""
    return {
        "configured": payment_service.api_key is not None,
        "provider": "stripe",
    }


@router.post("/create-intent")
async def create_payment_intent(
    request: PaymentIntentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a Stripe payment intent for an order."""
    order = db.query(Order).filter(Order.id == request.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    amount_cents = int(float(order.total_amount) * 100)
    result = await payment_service.create_payment_intent(
        amount=amount_cents,
        currency=request.currency,
        metadata={"order_id": str(order.id), "customer_name": order.customer_name or ""},
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Payment failed"))

    return result


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a Stripe checkout session for an order."""
    order = db.query(Order).filter(Order.id == request.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = []
    for item in order.items:
        items.append({
            "name": item.item_name,
            "price": float(item.unit_price),
            "quantity": item.quantity,
        })

    if not items:
        items.append({
            "name": f"Order #{order.id}",
            "price": float(order.total_amount),
            "quantity": 1,
        })

    result = await payment_service.create_checkout_session(
        items=items,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        customer_email=None,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Checkout failed"))

    return result


@router.get("/order/{order_id}")
async def get_order_payment_status(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get payment status for an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.id,
        "total_amount": float(order.total_amount),
        "order_status": order.status,
        "payment_configured": payment_service.api_key is not None,
    }
