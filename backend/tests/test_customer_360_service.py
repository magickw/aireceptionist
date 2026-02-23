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
        total_spent=5000.00,
        avg_sentiment=4.5,
        total_calls=5,
        last_interaction=datetime.now() - timedelta(days=7)
    )


class TestGetCustomerProfile:
    """Test cases for getting customer profiles"""
    
    @pytest.mark.asyncio
    async def test_get_customer_profile_success(self, customer_360_service, mock_db, sample_customer):
        """Test successful customer profile retrieval"""
        # Set up mock to return customer when queried
        mock_query_result = Mock()
        mock_query_result.first.return_value = sample_customer
        mock_db.query.return_value.filter.return_value = mock_query_result
        
        # Mock related data queries - return empty lists
        def mock_query_side_effect(model):
            mock_q = Mock()
            if model.__name__ == 'Customer':
                mock_q.filter.return_value = mock_query_result
            else:
                # For CallSession, Order, Appointment - return empty results
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
                mock_q.filter.return_value.order_by.return_value.all.return_value = []
            return mock_q
        
        mock_db.query.side_effect = mock_query_side_effect
        
        profile = await customer_360_service.get_customer_profile(
            db=mock_db,
            business_id=1,
            customer_phone="555-1234"
        )
        
        assert profile["customer"]["id"] == 1
        assert profile["customer"]["name"] == "John Doe"
        assert profile["customer"]["phone"] == "555-1234"
        assert profile["customer"]["loyalty_tier"] == "gold"
        assert profile["customer"]["is_vip"] is True
        assert "metrics" in profile
        assert "recent_activity" in profile
    
    @pytest.mark.asyncio
    async def test_get_customer_profile_not_found(self, customer_360_service, mock_db):
        """Test getting profile for non-existent customer"""
        mock_query_result = Mock()
        mock_query_result.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query_result
        
        profile = await customer_360_service.get_customer_profile(
            db=mock_db,
            business_id=1,
            customer_phone="999-9999"
        )
        
        assert "error" in profile
        assert profile["phone"] == "999-9999"


class TestGetCustomerInteractions:
    """Test cases for getting customer interactions"""
    
    @pytest.mark.asyncio
    async def test_get_customer_calls(self, customer_360_service, mock_db):
        """Test getting customer call history"""
        mock_calls = [
            Mock(id=1, started_at=datetime.now() - timedelta(days=1), sentiment="positive", duration_seconds=120, quality_score=0.9, summary="Test call"),
            Mock(id=2, started_at=datetime.now() - timedelta(days=7), sentiment="neutral", duration_seconds=90, quality_score=0.7, summary="Another test")
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_calls
        
        calls = await customer_360_service.get_customer_calls(
            customer_id=1,
            db=mock_db,
            limit=10
        )
        
        assert len(calls) == 2
        assert calls[0]["sentiment"] == "positive"
        assert calls[0]["duration"] == 120
    
    @pytest.mark.asyncio
    async def test_get_customer_appointments(self, customer_360_service, mock_db):
        """Test getting customer appointments"""
        mock_appointments = [
            Mock(
                id=1,
                appointment_time=datetime.now() + timedelta(days=1),
                status="confirmed",
                service_type="Consultation",
                notes="First visit"
            ),
            Mock(
                id=2,
                appointment_time=datetime.now() - timedelta(days=7),
                status="completed",
                service_type="Follow-up",
                notes="Checkup"
            )
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_appointments
        
        appointments = await customer_360_service.get_customer_appointments(
            customer_id=1,
            db=mock_db,
            limit=10
        )
        
        assert len(appointments) == 2
        assert appointments[0]["status"] == "confirmed"
        assert appointments[0]["service"] == "Consultation"
    
    @pytest.mark.asyncio
    async def test_get_customer_orders(self, customer_360_service, mock_db):
        """Test getting customer orders"""
        mock_orders = [
            Mock(
                id=1,
                created_at=datetime.now() - timedelta(days=2),
                total_amount=50.00,
                status="completed",
                delivery_method="pickup"
            ),
            Mock(
                id=2,
                created_at=datetime.now() - timedelta(days=10),
                total_amount=75.00,
                status="completed",
                delivery_method="delivery"
            )
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_orders
        
        orders = await customer_360_service.get_customer_orders(
            customer_id=1,
            db=mock_db,
            limit=10
        )
        
        assert len(orders) == 2
        assert orders[0]["total_amount"] == 50.00
        assert orders[0]["delivery_method"] == "pickup"


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
        # Recent interactions, positive sentiment
        mock_customer = Mock(
            last_interaction=datetime.now() - timedelta(days=3),
            avg_sentiment=0.8,
            total_calls=5,
            total_orders=3,
            total_appointments=2
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        
        churn_risk = await customer_360_service.calculate_churn_risk(
            customer_id=1,
            db=mock_db
        )
        
        assert churn_risk < 0.5  # Low risk
    
    @pytest.mark.asyncio
    async def test_calculate_churn_risk_high_risk(self, customer_360_service, mock_db):
        """Test churn risk calculation for high-risk customer"""
        # No recent interactions, low sentiment
        mock_customer = Mock(
            last_interaction=datetime.now() - timedelta(days=90),
            avg_sentiment=0.3,
            total_calls=0,
            total_orders=0,
            total_appointments=0
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        
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
        mock_customer = Mock(avg_sentiment=0.8)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        
        score = await customer_360_service.calculate_satisfaction_score(
            customer_id=1,
            db=mock_db
        )
        
        assert score > 4.0  # High satisfaction
    
    @pytest.mark.asyncio
    async def test_calculate_satisfaction_score_negative(self, customer_360_service, mock_db):
        """Test satisfaction score for negative customer"""
        mock_customer = Mock(avg_sentiment=0.3)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        
        score = await customer_360_service.calculate_satisfaction_score(
            customer_id=1,
            db=mock_db
        )
        
        assert score < 3.0  # Low satisfaction


class TestDetermineLoyaltyTier:
    """Test cases for determining loyalty tier"""
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_platinum(self, customer_360_service, mock_db):
        """Test platinum tier determination"""
        mock_customer = Mock(
            id=1,
            total_spent=5000.00,
            total_calls=30,
            total_orders=20
        )
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_customer
        mock_db.query.return_value = mock_query
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "platinum"  # $5000 + 50 interactions = platinum
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_gold(self, customer_360_service, mock_db):
        """Test gold tier determination"""
        mock_customer = Mock(
            id=1,
            total_spent=2500.00,
            total_calls=15,
            total_orders=10
        )
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_customer
        mock_db.query.return_value = mock_query
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "gold"  # $2500 + 25 interactions = gold
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_silver(self, customer_360_service, mock_db):
        """Test silver tier determination"""
        mock_customer = Mock(
            id=1,
            total_spent=750.00,
            total_calls=6,
            total_orders=4
        )
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_customer
        mock_db.query.return_value = mock_query
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "silver"  # $750 + 10 interactions = silver
    
    @pytest.mark.asyncio
    async def test_determine_loyalty_tier_standard(self, customer_360_service, mock_db):
        """Test standard tier determination"""
        mock_customer = Mock(
            id=1,
            total_spent=100.00,
            total_calls=2,
            total_orders=0
        )
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_customer
        mock_db.query.return_value = mock_query
        
        tier = await customer_360_service.determine_loyalty_tier(
            customer_id=1,
            db=mock_db
        )
        
        assert tier == "standard"  # $100 + 2 interactions = standard (not bronze)


class TestIdentifyVIPCustomers:
    """Test cases for identifying VIP customers"""
    
    @pytest.mark.asyncio
    async def test_identify_vip_high_value(self, customer_360_service, mock_db):
        """Test VIP identification for high-value customer"""
        mock_customer = Mock(
            lifetime_value=10000.00,
            satisfaction_score=4.8
        )
        
        is_vip = await customer_360_service.identify_vip(
            customer=mock_customer,
            db=mock_db
        )
        
        assert is_vip is True
    
    @pytest.mark.asyncio
    async def test_identify_vip_low_value(self, customer_360_service, mock_db):
        """Test VIP identification for low-value customer"""
        mock_customer = Mock(
            lifetime_value=100.00,
            satisfaction_score=3.0
        )
        
        is_vip = await customer_360_service.identify_vip(
            customer=mock_customer,
            db=mock_db
        )
        
        assert is_vip is False


class TestUpdateCustomerMetrics:
    """Test cases for updating customer metrics"""
    
    @pytest.mark.asyncio
    async def test_update_customer_metrics_success(self, customer_360_service, mock_db):
        """Test updating customer metrics"""
        mock_customer = Mock(
            id=1,
            name="John Doe",
            total_calls=5,
            total_orders=3,
            total_appointments=2,
            total_spent=500.00,
            avg_sentiment=0.7,
            avg_quality_score=0.8,
            last_interaction=datetime.now() - timedelta(days=1),
            churn_risk=0.2,
            is_vip=True,
            loyalty_tier="gold"
        )
        
        mock_calls = [
            Mock(id=1, customer_id=1, started_at=datetime.now() - timedelta(days=1), sentiment="positive", quality_score=0.8),
            Mock(id=2, customer_id=1, started_at=datetime.now() - timedelta(days=7), sentiment="neutral", quality_score=0.7)
        ]
        
        mock_orders = [
            Mock(id=1, customer_id=1, created_at=datetime.now() - timedelta(days=2), total_amount=150.00, status="completed"),
            Mock(id=2, customer_id=1, created_at=datetime.now() - timedelta(days=10), total_amount=200.00, status="completed")
        ]
        
        mock_appointments = [
            Mock(id=1, customer_id=1, appointment_time=datetime.now() - timedelta(days=3), service_type="Consultation")
        ]
        
        def mock_query_side_effect(model):
            mock_q = Mock()
            if model.__name__ == 'Customer':
                mock_q.filter.return_value.first.return_value = mock_customer
            elif model.__name__ == 'CallSession':
                mock_q.filter.return_value.all.return_value = mock_calls
            elif model.__name__ == 'Order':
                mock_q.filter.return_value.all.return_value = mock_orders
            elif model.__name__ == 'Appointment':
                mock_q.filter.return_value.all.return_value = mock_appointments
            return mock_q
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        result = await customer_360_service.update_customer_metrics(
            db=mock_db,
            customer_id=1
        )
        
        assert result["customer_id"] == 1
        assert "updated_metrics" in result
        assert result["updated_metrics"]["total_calls"] == 2


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