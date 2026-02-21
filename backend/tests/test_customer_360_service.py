"""Unit tests for Customer 360 Service"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from app.services.customer_360_service import Customer360Service
from app.models.models import Customer, CallSession, Appointment, Order


@pytest.fixture
def customer_360_service():
    """Create a Customer 360 service instance"""
    return Customer360Service()


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def sample_customer():
    """Sample customer for testing"""
    return Customer(
        id=1,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        loyalty_tier="gold",
        churn_risk=0.2,
        is_vip=True,
        lifetime_value=5000.00,
        satisfaction_score=4.5,
        complaint_count=0,
        call_count=5,
        last_contact=datetime.now() - timedelta(days=7)
    )


class TestGetCustomerProfile:
    """Test cases for getting customer profiles"""
    
    @pytest.mark.asyncio
    async def test_get_customer_profile_success(self, customer_360_service, mock_db, sample_customer):
        """Test successful customer profile retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_customer
        
        profile = await customer_360_service.get_customer_profile(
            customer_id=1,
            db=mock_db
        )
        
        assert profile["id"] == 1
        assert profile["name"] == "John Doe"
        assert profile["email"] == "john@example.com"
        assert profile["loyalty_tier"] == "gold"
        assert profile["is_vip"] is True
    
    @pytest.mark.asyncio
    async def test_get_customer_profile_not_found(self, customer_360_service, mock_db):
        """Test getting profile for non-existent customer"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        profile = await customer_360_service.get_customer_profile(
            customer_id=999,
            db=mock_db
        )
        
        assert profile is None


class TestGetCustomerInteractions:
    """Test cases for getting customer interactions"""
    
    @pytest.mark.asyncio
    async def test_get_customer_calls(self, customer_360_service, mock_db):
        """Test getting customer call history"""
        mock_calls = [
            Mock(id=1, call_date=datetime.now() - timedelta(days=1), sentiment="positive"),
            Mock(id=2, call_date=datetime.now() - timedelta(days=7), sentiment="neutral")
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_calls
        
        calls = await customer_360_service.get_customer_calls(
            customer_id=1,
            db=mock_db
        )
        
        assert len(calls) == 2
        assert calls[0]["sentiment"] == "positive"
    
    @pytest.mark.asyncio
    async def test_get_customer_appointments(self, customer_360_service, mock_db):
        """Test getting customer appointments"""
        mock_appointments = [
            Mock(
                id=1,
                start_time=datetime.now() + timedelta(days=1),
                status="confirmed",
                service="Consultation"
            ),
            Mock(
                id=2,
                start_time=datetime.now() - timedelta(days=7),
                status="completed",
                service="Follow-up"
            )
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_appointments
        
        appointments = await customer_360_service.get_customer_appointments(
            customer_id=1,
            db=mock_db
        )
        
        assert len(appointments) == 2
        assert appointments[0]["status"] == "confirmed"
    
    @pytest.mark.asyncio
    async def test_get_customer_orders(self, customer_360_service, mock_db):
        """Test getting customer orders"""
        mock_orders = [
            Mock(
                id=1,
                created_at=datetime.now() - timedelta(days=2),
                total_amount=50.00,
                status="completed"
            ),
            Mock(
                id=2,
                created_at=datetime.now() - timedelta(days=10),
                total_amount=75.00,
                status="completed"
            )
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_orders
        
        orders = await customer_360_service.get_customer_orders(
            customer_id=1,
            db=mock_db
        )
        
        assert len(orders) == 2
        assert orders[0]["total_amount"] == 50.00


class TestCalculateLifetimeValue:
    """Test cases for calculating customer lifetime value"""
    
    @pytest.mark.asyncio
    async def test_calculate_lifetime_value_with_orders(self, customer_360_service, mock_db):
        """Test LTV calculation with order history"""
        mock_orders = [
            Mock(total_amount=100.00),
            Mock(total_amount=150.00),
            Mock(total_amount=200.00)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_orders
        
        ltv = await customer_360_service.calculate_lifetime_value(
            customer_id=1,
            db=mock_db
        )
        
        assert ltv == 450.00
    
    @pytest.mark.asyncio
    async def test_calculate_lifetime_value_no_orders(self, customer_360_service, mock_db):
        """Test LTV calculation with no orders"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        ltv = await customer_360_service.calculate_lifetime_value(
            customer_id=1,
            db=mock_db
        )
        
        assert ltv == 0.00


class TestCalculateChurnRisk:
    """Test cases for calculating churn risk"""
    
    @pytest.mark.asyncio
    async def test_calculate_churn_risk_low_risk(self, customer_360_service, mock_db):
        """Test churn risk calculation for low-risk customer"""
        # Recent calls, positive sentiment
        mock_calls = [
            Mock(call_date=datetime.now() - timedelta(days=3), sentiment="positive"),
            Mock(call_date=datetime.now() - timedelta(days=10), sentiment="positive")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_calls
        
        churn_risk = await customer_360_service.calculate_churn_risk(
            customer_id=1,
            db=mock_db
        )
        
        assert churn_risk < 0.5  # Low risk
    
    @pytest.mark.asyncio
    async def test_calculate_churn_risk_high_risk(self, customer_360_service, mock_db):
        """Test churn risk calculation for high-risk customer"""
        # No recent calls, negative sentiment in past
        mock_calls = [
            Mock(call_date=datetime.now() - timedelta(days=60), sentiment="negative")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_calls
        
        churn_risk = await customer_360_service.calculate_churn_risk(
            customer_id=1,
            db=mock_db
        )
        
        assert churn_risk > 0.5  # High risk


class TestCalculateSatisfactionScore:
    """Test cases for calculating satisfaction score"""
    
    @pytest.mark.asyncio
    async def test_calculate_satisfaction_score_positive(self, customer_360_service, mock_db):
        """Test satisfaction score for positive customer"""
        mock_calls = [
            Mock(sentiment="positive"),
            Mock(sentiment="positive"),
            Mock(sentiment="neutral")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_calls
        
        score = await customer_360_service.calculate_satisfaction_score(
            customer_id=1,
            db=mock_db
        )
        
        assert score > 4.0  # High satisfaction
    
    @pytest.mark.asyncio
    async def test_calculate_satisfaction_score_negative(self, customer_360_service, mock_db):
        """Test satisfaction score for negative customer"""
        mock_calls = [
            Mock(sentiment="negative"),
            Mock(sentiment="negative"),
            Mock(sentiment="neutral")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_calls
        
        score = await customer_360_service.calculate_satisfaction_score(
            customer_id=1,
            db=mock_db
        )
        
        assert score < 3.0  # Low satisfaction


class TestDetermineLoyaltyTier:
    """Test cases for determining loyalty tier"""
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_gold(self, customer_360_service, mock_db):
        """Test gold tier determination"""
        mock_orders = [
            Mock(total_amount=500.00),
            Mock(total_amount=600.00)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_orders
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "gold"
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_silver(self, customer_360_service, mock_db):
        """Test silver tier determination"""
        mock_orders = [
            Mock(total_amount=200.00),
            Mock(total_amount=150.00)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_orders
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "silver"
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_bronze(self, customer_360_service, mock_db):
        """Test bronze tier determination"""
        mock_orders = [
            Mock(total_amount=50.00)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_orders
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "bronze"


class TestIdentifyVIPCustomers:
    """Test cases for identifying VIP customers"""
    
    @pytest.mark.asyncio
    async def test_identify_vip_high_value(self, customer_360_service, mock_db, sample_customer):
        """Test VIP identification for high-value customer"""
        sample_customer.lifetime_value = 10000.00
        sample_customer.satisfaction_score = 4.8
        
        is_vip = await customer_360_service.identify_vip(
            customer=sample_customer,
            db=mock_db
        )
        
        assert is_vip is True
    
    @pytest.mark.asyncio
    async def test_identify_vip_low_value(self, customer_360_service, mock_db, sample_customer):
        """Test VIP identification for low-value customer"""
        sample_customer.lifetime_value = 100.00
        sample_customer.satisfaction_score = 3.0
        
        is_vip = await customer_360_service.identify_vip(
            customer=sample_customer,
            db=mock_db
        )
        
        assert is_vip is False


class TestUpdateCustomerMetrics:
    """Test cases for updating customer metrics"""
    
    @pytest.mark.asyncio
    async def test_update_customer_metrics_after_call(self, customer_360_service, mock_db, sample_customer):
        """Test updating metrics after a call"""
        mock_call = Mock(
            id=1,
            customer_id=1,
            call_date=datetime.now(),
            sentiment="positive",
            duration=300
        )
        
        await customer_360_service.update_customer_metrics(
            customer=sample_customer,
            call=mock_call,
            db=mock_db
        )
        
        # Customer should be updated
        assert sample_customer.call_count >= 1
        assert sample_customer.last_contact is not None
    
    @pytest.mark.asyncio
    async def test_update_customer_metrics_after_order(self, customer_360_service, mock_db, sample_customer):
        """Test updating metrics after an order"""
        mock_order = Mock(
            id=1,
            customer_id=1,
            total_amount=150.00,
            created_at=datetime.now()
        )
        
        initial_ltv = sample_customer.lifetime_value
        
        await customer_360_service.update_customer_metrics(
            customer=sample_customer,
            order=mock_order,
            db=mock_db
        )
        
        # LTV should increase
        assert sample_customer.lifetime_value >= initial_ltv


class TestGetCustomerInsights:
    """Test cases for getting customer insights"""
    
    @pytest.mark.asyncio
    async def test_get_customer_insights_comprehensive(self, customer_360_service, mock_db):
        """Test comprehensive customer insights"""
        mock_customer = Mock(
            id=1,
            name="John Doe",
            email="john@example.com",
            loyalty_tier="gold",
            churn_risk=0.2,
            is_vip=True,
            lifetime_value=5000.00,
            satisfaction_score=4.5
        )
        
        mock_calls = [
            Mock(call_date=datetime.now() - timedelta(days=1), sentiment="positive")
        ]
        mock_orders = [
            Mock(total_amount=100.00),
            Mock(total_amount=200.00)
        ]
        
        # Setup mock queries
        def mock_query_side_effect(model):
            mock_query = Mock()
            if model == Customer:
                mock_query.filter.return_value.first.return_value = mock_customer
            elif model == CallSession:
                mock_query.filter.return_value.order_by.return_value.all.return_value = mock_calls
            elif model == Order:
                mock_query.filter.return_value.all.return_value = mock_orders
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        insights = await customer_360_service.get_customer_insights(
            customer_id=1,
            db=mock_db
        )
        
        assert insights["customer"]["name"] == "John Doe"
        assert insights["metrics"]["lifetime_value"] == 5000.00
        assert insights["metrics"]["satisfaction_score"] == 4.5
        assert insights["risk"]["churn_risk"] == 0.2
        assert insights["tier"] == "gold"
        assert insights["is_vip"] is True


class TestCustomerSegmentation:
    """Test cases for customer segmentation"""
    
    @pytest.mark.asyncio
    async def test_segment_customers_by_tier(self, customer_360_service, mock_db):
        """Test segmenting customers by loyalty tier"""
        mock_customers = [
            Mock(loyalty_tier="gold"),
            Mock(loyalty_tier="gold"),
            Mock(loyalty_tier="silver"),
            Mock(loyalty_tier="bronze")
        ]
        mock_db.query.return_value.all.return_value = mock_customers
        
        segments = await customer_360_service.segment_customers_by_tier(db=mock_db)
        
        assert segments["gold"] == 2
        assert segments["silver"] == 1
        assert segments["bronze"] == 1
    
    @pytest.mark.asyncio
    async def test_segment_customers_by_risk(self, customer_360_service, mock_db):
        """Test segmenting customers by churn risk"""
        mock_customers = [
            Mock(churn_risk=0.1),
            Mock(churn_risk=0.3),
            Mock(churn_risk=0.7),
            Mock(churn_risk=0.9)
        ]
        mock_db.query.return_value.all.return_value = mock_customers
        
        segments = await customer_360_service.segment_customers_by_risk(db=mock_db)
        
        assert segments["low"] == 2
        assert segments["medium"] == 1
        assert segments["high"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])