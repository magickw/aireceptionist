"""Unit tests for Payment Service"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.payment_service import PaymentService


@pytest.fixture
def payment_service():
    """Create a payment service instance"""
    return PaymentService()


class TestPaymentServiceInitialization:
    """Test cases for payment service initialization"""
    
    def test_initialization_with_stripe_key(self):
        """Test service initialization with Stripe key"""
        from app.core.config import settings
        
        service = PaymentService()
        
        # Service should have stripe configured
        assert hasattr(service, 'stripe')
        # Should be able to access stripe module
    
    def test_stripe_api_key_configuration(self):
        """Test Stripe API key configuration"""
        service = PaymentService()
        
        # Service should have access to Stripe configuration
        assert service.stripe is not None


class TestCreatePaymentIntent:
    """Test cases for creating payment intents"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_payment_intent_success(self, mock_stripe, payment_service):
        """Test successful payment intent creation"""
        # Mock Stripe response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd",
            customer_email="customer@example.com",
            metadata={"order_id": "order_123"}
        )
        
        assert result["success"] is True
        assert result["payment_intent_id"] == "pi_1234567890"
        assert result["amount"] == 1000
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_payment_intent_with_customer(self, mock_stripe, payment_service):
        """Test payment intent creation with existing customer"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_9876543210"
        mock_payment_intent.amount = 2500
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=2500,
            currency="usd",
            customer_id="cus_1234567890",
            metadata={"order_id": "order_456"}
        )
        
        assert result["success"] is True
        assert result["payment_intent_id"] == "pi_9876543210"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_payment_intent_error(self, mock_stripe, payment_service):
        """Test payment intent creation with error"""
        import stripe
        mock_stripe.PaymentIntent.create.side_effect = stripe.error.StripeError("Invalid amount")
        
        result = await payment_service.create_payment_intent(
            amount=-100,  # Invalid amount
            currency="usd"
        )
        
        assert result["success"] is False
        assert "error" in result


class TestCreateCheckoutSession:
    """Test cases for creating checkout sessions"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_checkout_session_success(self, mock_stripe, payment_service):
        """Test successful checkout session creation"""
        mock_session = Mock()
        mock_session.id = "cs_1234567890"
        mock_session.url = "https://checkout.stripe.com/pay/cs_1234567890"
        
        mock_stripe.checkout.Session.create.return_value = mock_session
        
        result = await payment_service.create_checkout_session(
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "Test Product"},
                        "unit_amount": 2000
                    },
                    "quantity": 1
                }
            ],
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert result["success"] is True
        assert result["session_id"] == "cs_1234567890"
        assert result["checkout_url"] is not None
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_checkout_session_with_customer(self, mock_stripe, payment_service):
        """Test checkout session with existing customer"""
        mock_session = Mock()
        mock_session.id = "cs_9876543210"
        mock_session.url = "https://checkout.stripe.com/pay/cs_9876543210"
        
        mock_stripe.checkout.Session.create.return_value = mock_session
        
        result = await payment_service.create_checkout_session(
            line_items=[
                {
                    "price": "price_1234567890",
                    "quantity": 2
                }
            ],
            customer_id="cus_1234567890",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert result["success"] is True


class TestRetrievePaymentIntent:
    """Test cases for retrieving payment intents"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_retrieve_payment_intent_success(self, mock_stripe, payment_service):
        """Test successful payment intent retrieval"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 1000
        
        mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent
        
        result = await payment_service.retrieve_payment_intent("pi_1234567890")
        
        assert result["success"] is True
        assert result["status"] == "succeeded"
        assert result["amount"] == 1000
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_retrieve_payment_intent_not_found(self, mock_stripe, payment_service):
        """Test retrieving non-existent payment intent"""
        import stripe
        mock_stripe.PaymentIntent.retrieve.side_effect = stripe.error.InvalidRequestError(
            "No such payment intent",
            "resource_missing"
        )
        
        result = await payment_service.retrieve_payment_intent("pi_nonexistent")
        
        assert result["success"] is False
        assert "error" in result


class TestProcessRefund:
    """Test cases for processing refunds"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_process_refund_success(self, mock_stripe, payment_service):
        """Test successful refund processing"""
        mock_refund = Mock()
        mock_refund.id = "re_1234567890"
        mock_refund.amount = 1000
        mock_refund.status = "succeeded"
        
        mock_stripe.Refund.create.return_value = mock_refund
        
        result = await payment_service.process_refund(
            payment_intent_id="pi_1234567890",
            amount=1000,
            reason="requested_by_customer"
        )
        
        assert result["success"] is True
        assert result["refund_id"] == "re_1234567890"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_process_refund_full_amount(self, mock_stripe, payment_service):
        """Test full refund without specifying amount"""
        mock_refund = Mock()
        mock_refund.id = "re_9876543210"
        mock_refund.amount = 2500
        mock_refund.status = "succeeded"
        
        mock_stripe.Refund.create.return_value = mock_refund
        
        result = await payment_service.process_refund(
            payment_intent_id="pi_1234567890",
            reason="requested_by_customer"
        )
        
        assert result["success"] is True


class TestCreateCustomer:
    """Test cases for creating customers"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_customer_success(self, mock_stripe, payment_service):
        """Test successful customer creation"""
        mock_customer = Mock()
        mock_customer.id = "cus_1234567890"
        mock_customer.email = "customer@example.com"
        mock_customer.name = "John Doe"
        
        mock_stripe.Customer.create.return_value = mock_customer
        
        result = await payment_service.create_customer(
            email="customer@example.com",
            name="John Doe",
            phone="555-1234"
        )
        
        assert result["success"] is True
        assert result["customer_id"] == "cus_1234567890"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_create_customer_with_payment_method(self, mock_stripe, payment_service):
        """Test customer creation with payment method"""
        mock_customer = Mock()
        mock_customer.id = "cus_9876543210"
        mock_customer.email = "customer@example.com"
        
        mock_stripe.Customer.create.return_value = mock_customer
        
        result = await payment_service.create_customer(
            email="customer@example.com",
            payment_method_id="pm_1234567890"
        )
        
        assert result["success"] is True


class TestPaymentValidation:
    """Test cases for payment validation"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_validate_payment_amount_positive(self, mock_stripe, payment_service):
        """Test payment amount validation (positive amount)"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=100,  # Valid positive amount
            currency="usd"
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_validate_minimum_amount(self, mock_stripe, payment_service):
        """Test minimum payment amount validation"""
        import stripe
        # Stripe minimum is $0.50 (50 cents)
        mock_stripe.PaymentIntent.create.side_effect = stripe.error.InvalidRequestError(
            "Amount must be at least 50 cents",
            "amount_too_small"
        )
        
        result = await payment_service.create_payment_intent(
            amount=10,  # Below minimum
            currency="usd"
        )
        
        assert result["success"] is False


class TestPaymentMetadata:
    """Test cases for payment metadata handling"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_payment_intent_with_metadata(self, mock_stripe, payment_service):
        """Test payment intent with metadata"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.metadata = {"order_id": "order_123", "customer_type": "vip"}
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd",
            metadata={"order_id": "order_123", "customer_type": "vip"}
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_checkout_session_with_metadata(self, mock_stripe, payment_service):
        """Test checkout session with metadata"""
        mock_session = Mock()
        mock_session.id = "cs_1234567890"
        mock_session.url = "https://checkout.stripe.com/pay/cs_1234567890"
        
        mock_stripe.checkout.Session.create.return_value = mock_session
        
        result = await payment_service.create_checkout_session(
            line_items=[{"price": "price_123", "quantity": 1}],
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            metadata={"source": "ai_receptionist"}
        )
        
        assert result["success"] is True


class TestPaymentErrorHandling:
    """Test cases for payment error handling"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_handle_stripe_card_error(self, mock_stripe, payment_service):
        """Test handling Stripe card errors"""
        import stripe
        mock_stripe.PaymentIntent.create.side_effect = stripe.error.CardError(
            "Your card was declined",
            "card_declined",
            "decline_code"
        )
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd"
        )
        
        assert result["success"] is False
        assert "card" in result["error"].lower()
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe')
    async def test_handle_stripe_api_error(self, mock_stripe, payment_service):
        """Test handling Stripe API errors"""
        import stripe
        mock_stripe.PaymentIntent.create.side_effect = stripe.error.APIError(
            "An error occurred with our API"
        )
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd"
        )
        
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])