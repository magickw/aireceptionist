"""Unit tests for Nova Reasoning Engine"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.nova_reasoning import NovaReasoningEngine, get_training_context
from app.models.models import AITrainingScenario


@pytest.fixture
def reasoning_engine():
    """Create a reasoning engine instance"""
    return NovaReasoningEngine()


@pytest.fixture
def sample_business_context():
    """Sample business context for testing"""
    return {
        "business_id": 1,
        "name": "Test Restaurant",
        "type": "restaurant",
        "services": ["dine-in", "takeout", "delivery"],
        "operating_hours": {"monday": "9am-9pm", "tuesday": "9am-9pm"},
        "menu": [
            {"name": "Burger", "price": 12.99, "category": "Main Course"},
            {"name": "Salad", "price": 8.99, "category": "Appetizer"}
        ],
        "available_slots": ["10am", "2pm", "5pm"]
    }


@pytest.fixture
def sample_customer_context():
    """Sample customer context for testing"""
    return {
        "name": "John Doe",
        "phone": "555-1234",
        "email": "john@example.com",
        "call_count": 3,
        "last_contact": "2024-01-15",
        "satisfaction_score": 4.2,
        "preferred_services": ["dine-in"],
        "complaint_count": 0
    }


class TestDeterministicTriggers:
    """Test cases for deterministic safety triggers"""
    
    def test_critical_keyword_detection(self, reasoning_engine):
        """Test detection of critical keywords"""
        conversation = "This is terrible, I'm going to sue you"
        customer_context = {"complaint_count": 0, "satisfaction_score": 3.0}
        
        result = reasoning_engine._check_deterministic_triggers(
            conversation, customer_context, "restaurant"
        )
        
        assert result["should_escalate"] is True
        assert "sue" in result["reason"].lower()
        assert result["trigger_type"] == "critical_keyword"
    
    def test_emergency_keyword_detection(self, reasoning_engine):
        """Test detection of emergency keywords"""
        conversation = "There's a gas leak, please help!"
        customer_context = {"complaint_count": 0, "satisfaction_score": 3.0}
        
        result = reasoning_engine._check_deterministic_triggers(
            conversation, customer_context, "hvac"
        )
        
        assert result["should_escalate"] is True
        assert result["requires_911"] is True
        assert result["trigger_type"] == "safety_emergency"
    
    def test_medical_emergency_detection(self, reasoning_engine):
        """Test detection of medical emergency indicators"""
        conversation = "I have severe chest pain and can't breathe"
        customer_context = {"complaint_count": 0, "satisfaction_score": 3.0}
        
        result = reasoning_engine._check_deterministic_triggers(
            conversation, customer_context, "medical"
        )
        
        assert result["should_escalate"] is True
        assert result["requires_911"] is True
        assert result["trigger_type"] == "medical_emergency"
    
    def test_vip_customer_with_complaint(self, reasoning_engine):
        """Test VIP customer with negative sentiment"""
        conversation = "I'm very unhappy with the service"
        customer_context = {
            "complaint_count": 1,
            "satisfaction_score": 4.7  # VIP threshold is 4.5
        }
        
        result = reasoning_engine._check_deterministic_triggers(
            conversation, customer_context, "restaurant"
        )
        
        assert result["should_escalate"] is True
        assert result["trigger_type"] == "vip_concern"
        assert result["satisfaction_score"] == 4.7
    
    def test_repeat_complaint_pattern(self, reasoning_engine):
        """Test repeat complaint pattern detection"""
        conversation = "I want to speak to a manager about this"
        customer_context = {
            "complaint_count": 3,  # Above threshold of 2
            "satisfaction_score": 3.0
        }
        
        result = reasoning_engine._check_deterministic_triggers(
            conversation, customer_context, "restaurant"
        )
        
        assert result["should_escalate"] is True
        assert result["trigger_type"] == "repeat_complaint"
        assert result["complaint_count"] == 3
    
    def test_no_triggers(self, reasoning_engine):
        """Test normal conversation without triggers"""
        conversation = "I'd like to make a reservation for tomorrow"
        customer_context = {"complaint_count": 0, "satisfaction_score": 4.0}
        
        result = reasoning_engine._check_deterministic_triggers(
            conversation, customer_context, "restaurant"
        )
        
        assert result["should_escalate"] is False
        assert result["reason"] is None


class TestDeterministicEscalationResponse:
    """Test cases for deterministic escalation responses"""
    
    def test_emergency_response_creation(self, reasoning_engine, sample_business_context, sample_customer_context):
        """Test creation of emergency escalation response"""
        trigger_info = {
            "should_escalate": True,
            "reason": "Gas leak detected",
            "trigger_type": "safety_emergency",
            "requires_911": True
        }
        
        response = reasoning_engine._create_deterministic_escalation_response(
            trigger_info, sample_business_context, sample_customer_context
        )
        
        assert response["selected_action"] == "HUMAN_INTERVENTION"
        assert response["requires_approval"] is True
        assert "911" in response["suggested_response"] or "evacuate" in response["suggested_response"]
        assert response["deterministic_trigger"] is True
    
    def test_medical_emergency_response(self, reasoning_engine, sample_business_context, sample_customer_context):
        """Test medical emergency response"""
        trigger_info = {
            "should_escalate": True,
            "reason": "Chest pain detected",
            "trigger_type": "medical_emergency",
            "requires_911": True
        }
        
        response = reasoning_engine._create_deterministic_escalation_response(
            trigger_info, sample_business_context, sample_customer_context
        )
        
        assert "911" in response["suggested_response"] or "emergency room" in response["suggested_response"]


class TestAvailableActions:
    """Test available actions validation"""
    
    def test_valid_actions_list(self, reasoning_engine):
        """Test that all available actions are valid"""
        expected_actions = [
            "CREATE_APPOINTMENT",
            "PROVIDE_INFO",
            "TRANSFER_HUMAN",
            "UPDATE_CRM",
            "HANDLE_COMPLAINT",
            "COLLECT_INFO",
            "RESCHEDULE_APPOINTMENT",
            "CANCEL_APPOINTMENT",
            "TAKE_MESSAGE",
            "PAYMENT_PROCESS",
            "SEND_DIRECTIONS",
            "PLACE_ORDER",
            "CONFIRM_ORDER",
            "HUMAN_INTERVENTION"
        ]
        
        assert reasoning_engine.available_actions == expected_actions


class TestReasoningChain:
    """Test reasoning chain generation"""
    
    def test_reasoning_chain_structure(self, reasoning_engine, sample_business_context, sample_customer_context):
        """Test reasoning chain has correct structure"""
        reasoning_result = {
            "intent": "order_food",
            "confidence": 0.85,
            "selected_action": "PLACE_ORDER",
            "entities": {"menu_item": "Burger"}
        }
        
        chain = reasoning_engine._build_reasoning_chain(
            reasoning_result, sample_business_context, sample_customer_context
        )
        
        assert isinstance(chain, list)
        assert len(chain) > 0
        assert all("step" in item for item in chain)
        assert all("title" in item for item in chain)


class TestTrainingContext:
    """Test training context retrieval"""
    
    @pytest.mark.asyncio
    async def test_get_training_context_with_db(self):
        """Test getting training context from database"""
        # Mock database session
        mock_db = Mock()
        mock_scenario = AITrainingScenario(
            id=1,
            business_id=1,
            user_input="I want to order a pizza",
            expected_response="Great choice! What toppings would you like?",
            category="order",
            is_active=True
        )
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_scenario]
        mock_db.query.return_value = mock_query
        
        result = await get_training_context(
            business_id=1,
            db=mock_db,
            conversation="I want to order a pizza"
        )
        
        assert "Training Examples" in result
        assert "pizza" in result.lower()
    
    @pytest.mark.asyncio
    async def test_get_training_context_no_scenarios(self):
        """Test getting training context with no scenarios"""
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = await get_training_context(
            business_id=1,
            db=mock_db,
            conversation="Hello"
        )
        
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_get_training_context_no_db(self):
        """Test getting training context without database"""
        result = await get_training_context(
            business_id=1,
            db=None,
            conversation="Hello"
        )
        
        assert result == ""


class TestFallbackResponse:
    """Test fallback response generation"""
    
    def test_fallback_response_structure(self, reasoning_engine):
        """Test fallback response has correct structure"""
        error_message = "Connection timeout"
        
        fallback = reasoning_engine._get_fallback_response(error_message)
        
        assert fallback["selected_action"] == "HUMAN_INTERVENTION"
        assert fallback["requires_approval"] is True
        assert fallback["confidence"] == 0.0
        assert fallback["intent"] == "error"


class TestResponseQualityEvaluation:
    """Test LLM-as-a-Judge response evaluation"""
    
    @pytest.mark.asyncio
    @patch.object(NovaReasoningEngine, '_invoke_nova_lite')
    async def test_evaluate_response_quality_success(self, mock_invoke, reasoning_engine):
        """Test successful response quality evaluation"""
        mock_invoke.return_value = {"score": 85, "reasoning": "Good match"}
        
        score = await reasoning_engine.evaluate_response_quality(
            user_input="What are your hours?",
            expected_response="We're open from 9am to 9pm",
            actual_response="Our hours are 9am to 9pm"
        )
        
        assert score == 85.0
    
    @pytest.mark.asyncio
    @patch.object(NovaReasoningEngine, '_invoke_nova_lite')
    async def test_evaluate_response_quality_error(self, mock_invoke, reasoning_engine):
        """Test response quality evaluation with error"""
        mock_invoke.side_effect = Exception("API error")
        
        score = await reasoning_engine.evaluate_response_quality(
            user_input="Hello",
            expected_response="Hi there!",
            actual_response="Hello"
        )
        
        assert score == 0.0


class TestSyntheticTrainingData:
    """Test synthetic training data generation"""
    
    @pytest.mark.asyncio
    @patch.object(NovaReasoningEngine, '_invoke_nova_lite')
    async def test_generate_synthetic_training_data_success(self, mock_invoke, reasoning_engine):
        """Test successful synthetic training data generation"""
        mock_invoke.return_value = '''[
            {"user_input": "I need a haircut", "expected_response": "I can schedule that for you", "category": "appointment_booking"},
            {"user_input": "How much for a trim?", "expected_response": "A trim costs $25", "category": "sales_inquiry"}
        ]'''
        
        scenarios = await reasoning_engine.generate_synthetic_training_data(
            business_type="salon",
            services=["haircut", "coloring"],
            count=2
        )
        
        assert len(scenarios) == 2
        assert all("user_input" in s for s in scenarios)
        assert all("expected_response" in s for s in scenarios)
        assert all("category" in s for s in scenarios)
    
    @pytest.mark.asyncio
    @patch.object(NovaReasoningEngine, '_invoke_nova_lite')
    async def test_generate_synthetic_training_data_error(self, mock_invoke, reasoning_engine):
        """Test synthetic training data generation with error"""
        mock_invoke.side_effect = Exception("API error")
        
        scenarios = await reasoning_engine.generate_synthetic_training_data(
            business_type="restaurant",
            services=["dine-in"],
            count=5
        )
        
        assert scenarios == []


class TestThresholdDefaults:
    """Test default threshold values"""
    
    def test_default_confidence_threshold(self, reasoning_engine):
        """Test default confidence threshold"""
        assert reasoning_engine.DEFAULT_CONFIDENCE_THRESHOLD == 0.85
    
    def test_default_risk_threshold(self, reasoning_engine):
        """Test default risk threshold"""
        assert reasoning_engine.DEFAULT_RISK_THRESHOLD == 0.7
    
    def test_vip_satisfaction_threshold(self, reasoning_engine):
        """Test VIP satisfaction threshold"""
        assert reasoning_engine.VIP_SATISFACTION_THRESHOLD == 4.5
    
    def test_repeat_complaint_threshold(self, reasoning_engine):
        """Test repeat complaint threshold"""
        assert reasoning_engine.REPEAT_COMPLAINT_THRESHOLD == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])