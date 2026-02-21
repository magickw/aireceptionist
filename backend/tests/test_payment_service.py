"""Unit tests for Payment Service"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os
from app.core.config import settings
from app.services.payment_service import PaymentService


@pytest.fixture
def payment_service():
    """Create a payment service instance with test key"""
    # Mock settings to return test key
    with patch.object(settings, 'STRIPE_SECRET_KEY', 'sk_test_1234567890'):
        service = PaymentService()
        return service


class TestPaymentServiceInitialization:
    """Test cases for payment service initialization"""
    
    def test_initialization_with_stripe_key(self, payment_service):
        """Test service initialization with Stripe key"""
        assert payment_service.api_key is not None
        assert payment_service.api_key == 'sk_test_1234567890'
    
    def test_initialization_without_stripe_key(self):
        """Test service initialization without Stripe key"""
        with patch.dict(os.environ, {}, clear=True):
            service = PaymentService()
            assert service.api_key is None


class TestCreatePaymentIntent:
    """Test cases for creating payment intents"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    @patch('app.services.payment_service.stripe.Customer.list')
    @patch('app.services.payment_service.stripe.Customer.create')
    async def test_create_payment_intent_success(self, mock_customer_create, mock_customer_list, mock_intent_create, payment_service):
        """Test successful payment intent creation"""
        # Mock Stripe response
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.client_secret = "pi_1234567890_secret_abc123"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_intent_create.return_value = mock_payment_intent
        mock_customer_list.return_value.data = []
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd",
            customer_email="customer@example.com",
            metadata={"order_id": "order_123"}
        )
        
        assert result["success"] is True
        assert result["intent_id"] == "pi_1234567890"
        assert result["amount"] == 1000
        assert result["currency"] == "usd"
        assert result["status"] == "requires_payment_method"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_create_payment_intent_without_customer(self, mock_intent_create, payment_service):
        """Test payment intent creation without customer email"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_9876543210"
        mock_payment_intent.client_secret = "pi_9876543210_secret_xyz789"
        mock_payment_intent.amount = 2500
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_intent_create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=2500,
            currency="usd",
            metadata={"order_id": "order_456"}
        )
        
        assert result["success"] is True
        assert result["intent_id"] == "pi_9876543210"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_create_payment_intent_error(self, mock_intent_create, payment_service):
        """Test payment intent creation with error"""
        import stripe
        mock_intent_create.side_effect = stripe.error.StripeError("Invalid amount")
        
        result = await payment_service.create_payment_intent(
            amount=-100,
            currency="usd"
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_not_configured(self):
        """Test payment intent creation without Stripe configured"""
        with patch.dict(os.environ, {}, clear=True):
            service = PaymentService()
            result = await service.create_payment_intent(amount=1000, currency="usd")
            
            assert result["success"] is False
            assert "Stripe not configured" in result["error"]
    
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
    @patch('app.services.payment_service.stripe.checkout.Session.create')
    @patch('app.services.payment_service.stripe.Customer.list')
    @patch('app.services.payment_service.stripe.Customer.create')
    async def test_create_checkout_session_success(self, mock_customer_create, mock_customer_list, mock_session_create, payment_service):
        """Test successful checkout session creation"""
        mock_session = Mock()
        mock_session.id = "cs_1234567890"
        mock_session.url = "https://checkout.stripe.com/pay/cs_1234567890"
        
        mock_session_create.return_value = mock_session
        mock_customer_list.return_value.data = []
        
        result = await payment_service.create_checkout_session(
            items=[
                {
                    "name": "Test Product",
                    "price": 20.00,
                    "quantity": 1
                }
            ],
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert result["success"] is True
        assert result["session_id"] == "cs_1234567890"
        assert result["url"] == "https://checkout.stripe.com/pay/cs_1234567890"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.checkout.Session.create')
    @patch('app.services.payment_service.stripe.Customer.list')
    async def test_create_checkout_session_with_customer(self, mock_customer_list, mock_session_create, payment_service):
        """Test checkout session with existing customer"""
        mock_session = Mock()
        mock_session.id = "cs_9876543210"
        mock_session.url = "https://checkout.stripe.com/pay/cs_9876543210"
        
        mock_session_create.return_value = mock_session
        
        mock_customer = Mock()
        mock_customer.id = "cus_1234567890"
        mock_customer_list.return_value.data = [mock_customer]
        
        result = await payment_service.create_checkout_session(
            items=[
                {
                    "name": "Test Product",
                    "price": 25.00,
                    "quantity": 2
                }
            ],
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_email="existing@example.com"
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_not_configured(self):
        """Test checkout session creation without Stripe configured"""
        with patch.dict(os.environ, {}, clear=True):
            service = PaymentService()
            result = await service.create_checkout_session(
                items=[{"name": "Test", "price": 10, "quantity": 1}],
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
            
            assert result["success"] is False


class TestRetrievePayment:
    """Test cases for retrieving payment intents"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.retrieve')
    async def test_retrieve_payment_success(self, mock_retrieve, payment_service):
        """Test successful payment intent retrieval"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.created = 1234567890
        mock_payment_intent.metadata = {"order_id": "order_123"}
        
        mock_retrieve.return_value = mock_payment_intent
        
        result = await payment_service.retrieve_payment("pi_1234567890")
        
        assert result["success"] is True
        assert result["intent_id"] == "pi_1234567890"
        assert result["status"] == "succeeded"
        assert result["amount"] == 1000
        assert result["currency"] == "usd"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.retrieve')
    async def test_retrieve_payment_not_found(self, mock_retrieve, payment_service):
        """Test retrieving non-existent payment intent"""
        import stripe
        mock_retrieve.side_effect = stripe.error.InvalidRequestError(
            "No such payment intent",
            "resource_missing"
        )
        
        result = await payment_service.retrieve_payment("pi_nonexistent")
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_retrieve_payment_not_configured(self):
        """Test payment retrieval without Stripe configured"""
        with patch.dict(os.environ, {}, clear=True):
            service = PaymentService()
            result = await service.retrieve_payment("pi_1234567890")
            
            assert result["success"] is False


class TestProcessRefund:
    """Test cases for processing refunds"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.Refund.create')
    @patch('app.services.payment_service.stripe.PaymentIntent.retrieve')
    async def test_process_refund_success(self, mock_retrieve, mock_refund_create, payment_service):
        """Test successful refund processing"""
        mock_refund = Mock()
        mock_refund.id = "re_1234567890"
        mock_refund.amount = 1000
        mock_refund.status = "succeeded"
        
        mock_refund_create.return_value = mock_refund
        
        result = await payment_service.process_refund(
            payment_intent_id="pi_1234567890",
            amount=1000,
            reason="requested_by_customer"
        )
        
        assert result["success"] is True
        assert result["refund_id"] == "re_1234567890"
        assert result["amount"] == 1000
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.Refund.create')
    @patch('app.services.payment_service.stripe.PaymentIntent.retrieve')
    async def test_process_refund_full_amount(self, mock_retrieve, mock_refund_create, payment_service):
        """Test full refund without specifying amount"""
        mock_payment_intent = Mock()
        mock_payment_intent.amount = 2500
        
        mock_refund = Mock()
        mock_refund.id = "re_9876543210"
        mock_refund.amount = 2500
        mock_refund.status = "succeeded"
        
        mock_retrieve.return_value = mock_payment_intent
        mock_refund_create.return_value = mock_refund
        
        result = await payment_service.process_refund(
            payment_intent_id="pi_1234567890",
            reason="requested_by_customer"
        )
        
        assert result["success"] is True
        assert result["amount"] == 2500
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.Refund.create')
    async def test_process_refund_with_reason(self, mock_refund_create, payment_service):
        """Test refund with reason"""
        mock_refund = Mock()
        mock_refund.id = "re_5555555555"
        mock_refund.amount = 500
        mock_refund.status = "succeeded"
        
        mock_refund_create.return_value = mock_refund
        
        result = await payment_service.process_refund(
            payment_intent_id="pi_1234567890",
            amount=500,
            reason="duplicate"
        )
        
        assert result["success"] is True
        assert result["refund_id"] == "re_5555555555"
    
    @pytest.mark.asyncio
    async def test_process_refund_not_configured(self):
        """Test refund processing without Stripe configured"""
        with patch.dict(os.environ, {}, clear=True):
            service = PaymentService()
            result = await service.process_refund(
                payment_intent_id="pi_1234567890",
                amount=1000
            )
            
            assert result["success"] is False


class TestCustomerManagement:
    """Test cases for customer management"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.Customer.list')
    @patch('app.services.payment_service.stripe.Customer.create')
    async def test_get_or_create_customer_new(self, mock_customer_create, mock_customer_list, payment_service):
        """Test creating a new customer"""
        mock_customer = Mock()
        mock_customer.id = "cus_1234567890"
        mock_customer.email = "new@example.com"
        
        mock_customer_list.return_value.data = []
        mock_customer_create.return_value = mock_customer
        
        result = await payment_service._get_or_create_customer("new@example.com")
        
        assert result is not None
        assert result.id == "cus_1234567890"
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.Customer.list')
    async def test_get_or_create_customer_existing(self, mock_customer_list, payment_service):
        """Test getting an existing customer"""
        mock_customer = Mock()
        mock_customer.id = "cus_9876543210"
        mock_customer.email = "existing@example.com"
        
        mock_customer_list.return_value.data = [mock_customer]
        
        result = await payment_service._get_or_create_customer("existing@example.com")
        
        assert result is not None
        assert result.id == "cus_9876543210"


class TestPaymentValidation:
    """Test cases for payment validation"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_validate_payment_amount_positive(self, mock_intent_create, payment_service):
        """Test payment amount validation (positive amount)"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.client_secret = "pi_1234567890_secret_abc123"
        mock_payment_intent.status = "requires_payment_method"
        
        mock_intent_create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=100,
            currency="usd"
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_validate_minimum_amount(self, mock_intent_create, payment_service):
        """Test minimum payment amount validation"""
        import stripe
        mock_intent_create.side_effect = stripe.error.InvalidRequestError(
            "Amount must be at least 50 cents",
            "amount_too_small"
        )
        
        result = await payment_service.create_payment_intent(
            amount=10,
            currency="usd"
        )
        
        assert result["success"] is False


class TestPaymentMetadata:
    """Test cases for payment metadata handling"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_payment_intent_with_metadata(self, mock_intent_create, payment_service):
        """Test payment intent with metadata"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = "pi_1234567890"
        mock_payment_intent.client_secret = "pi_1234567890_secret_abc123"
        mock_payment_intent.status = "requires_payment_method"
        mock_payment_intent.metadata = {"order_id": "order_123", "customer_type": "vip"}
        
        mock_intent_create.return_value = mock_payment_intent
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd",
            metadata={"order_id": "order_123", "customer_type": "vip"}
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.checkout.Session.create')
    async def test_checkout_session_with_multiple_items(self, mock_session_create, payment_service):
        """Test checkout session with multiple items"""
        mock_session = Mock()
        mock_session.id = "cs_1234567890"
        mock_session.url = "https://checkout.stripe.com/pay/cs_1234567890"
        
        mock_session_create.return_value = mock_session
        
        result = await payment_service.create_checkout_session(
            items=[
                {"name": "Product 1", "price": 10.00, "quantity": 2},
                {"name": "Product 2", "price": 15.00, "quantity": 1}
            ],
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert result["success"] is True


class TestPaymentErrorHandling:
    """Test cases for payment error handling"""
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_handle_stripe_card_error(self, mock_intent_create, payment_service):
        """Test handling Stripe card errors"""
        import stripe
        mock_intent_create.side_effect = stripe.error.CardError(
            "Your card was declined",
            "card_declined",
            "decline_code"
        )
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd"
        )
        
        assert result["success"] is False
    
    @pytest.mark.asyncio
    @patch('app.services.payment_service.stripe.PaymentIntent.create')
    async def test_handle_stripe_api_error(self, mock_intent_create, payment_service):
        """Test handling Stripe API errors"""
        import stripe
        mock_intent_create.side_effect = stripe.error.APIError(
            "An error occurred with our API"
        )
        
        result = await payment_service.create_payment_intent(
            amount=1000,
            currency="usd"
        )
        
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])