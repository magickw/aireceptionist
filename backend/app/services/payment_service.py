"""
Payment Service using Stripe
Handles payment processing for orders
"""

import stripe
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.config import settings

class PaymentService:
    """Service for payment processing using Stripe"""
    
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else os.environ.get('STRIPE_SECRET_KEY')
        if self.api_key:
            stripe.api_key = self.api_key
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        metadata: Optional[Dict[str, str]] = None,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Stripe payment intent"""
        if not self.api_key:
            return {
                "success": False,
                "error": "Stripe not configured"
            }
        
        try:
            intent_params = {
                "amount": amount,
                "currency": currency,
                "metadata": metadata or {}
            }
            
            if customer_email:
                # Create or get customer
                customer = await self._get_or_create_customer(customer_email)
                intent_params["customer"] = customer.id
            
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            return {
                "success": True,
                "intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount,
                "currency": currency,
                "status": payment_intent.status
            }
        except Exception as e:
            print(f"[Payment Service] Failed to create payment intent: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_or_create_customer(self, email: str) -> Any:
        """Get or create a Stripe customer"""
        try:
            # Try to find existing customer
            customers = stripe.Customer.list(email=email).data
            if customers:
                return customers[0]
            
            # Create new customer
            return stripe.Customer.create(email=email)
        except Exception as e:
            print(f"[Payment Service] Failed to get/create customer: {e}")
            return None
    
    async def retrieve_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Retrieve payment intent details"""
        if not self.api_key:
            return {
                "success": False,
                "error": "Stripe not configured"
            }
        
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "success": True,
                "intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "created": payment_intent.created,
                "metadata": payment_intent.metadata
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_checkout_session(
        self,
        items: List[Dict[str, Any]],
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session"""
        if not self.api_key:
            return {
                "success": False,
                "error": "Stripe not configured"
            }
        
        try:
            line_items = []
            for item in items:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": item["name"]
                        },
                        "unit_amount": int(item["price"] * 100)
                    },
                    "quantity": item.get("quantity", 1)
                })
            
            session_params = {
                "payment_method_types": ["card"],
                "line_items": line_items,
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url
            }
            
            if customer_email:
                customer = await self._get_or_create_customer(customer_email)
                session_params["customer"] = customer.id
            
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a refund"""
        if not self.api_key:
            return {
                "success": False,
                "error": "Stripe not configured"
            }
        
        try:
            refund_params = {"payment_intent": payment_intent_id}
            
            if amount:
                refund_params["amount"] = amount
            else:
                refund_params["amount"] = (await self.retrieve_payment(payment_intent_id))["amount"]
            
            if reason:
                refund_params["reason"] = reason
            
            refund = stripe.Refund.create(**refund_params)
            
            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount,
                "status": refund.status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
payment_service = PaymentService()
