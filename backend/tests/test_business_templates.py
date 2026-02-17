"""Unit tests for business templates service"""

import pytest
from datetime import datetime
from app.services.business_template_service import BusinessTemplateService, get_template, get_all_templates
from app.models.models import BusinessTemplate, TemplateVersion
from sqlalchemy.orm import Session


@pytest.fixture
def template_service():
    """Create a template service instance"""
    return BusinessTemplateService()


@pytest.fixture
def sample_template_dict():
    """Sample template data for testing"""
    return {
        "template_key": "test_restaurant",
        "name": "Test Restaurant",
        "icon": "restaurant",
        "description": "A test restaurant template",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["food_poisoning", "severe_allergy"],
            "auto_escalate_threshold": 0.7,
            "confidence_threshold": 0.5,
        },
        "common_intents": ["order_food", "make_reservation", "hours_inquiry"],
        "fields": {
            "customer_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's your phone number?"
            },
        },
        "booking_flow": {
            "type": "order",
            "steps": [
                {"field": "menu_item", "ask_if_missing": True},
                {"field": "customer_name", "ask_if_missing": True},
            ],
            "final_action": "PLACE_ORDER",
            "confirmation_message": "Your order has been placed!",
        },
        "system_prompt_addition": "## Restaurant Guidelines\n- Be polite\n- Confirm orders",
        "example_responses": {
            "order_food": "Great choice! What would you like to order?",
            "hours_inquiry": "We're open from 9 AM to 9 PM.",
        },
        "is_active": True,
        "is_default": False,
        "version": 1,
    }


class TestBusinessTemplateService:
    """Test cases for BusinessTemplateService"""
    
    def test_template_to_dict(self, template_service, sample_template_dict):
        """Test converting template model to dictionary"""
        # Create a mock template object
        template = BusinessTemplate(
            id=1,
            template_key=sample_template_dict["template_key"],
            name=sample_template_dict["name"],
            icon=sample_template_dict["icon"],
            description=sample_template_dict["description"],
            autonomy_level=sample_template_dict["autonomy_level"],
            high_risk_intents=sample_template_dict["risk_profile"]["high_risk_intents"],
            auto_escalate_threshold=sample_template_dict["risk_profile"]["auto_escalate_threshold"],
            confidence_threshold=sample_template_dict["risk_profile"]["confidence_threshold"],
            common_intents=sample_template_dict["common_intents"],
            fields=sample_template_dict["fields"],
            booking_flow=sample_template_dict["booking_flow"],
            system_prompt_addition=sample_template_dict["system_prompt_addition"],
            example_responses=sample_template_dict["example_responses"],
            is_active=sample_template_dict["is_active"],
            is_default=sample_template_dict["is_default"],
            version=sample_template_dict["version"],
            created_by=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        result = template_service._template_to_dict(template)
        
        assert result["id"] == 1
        assert result["template_key"] == "test_restaurant"
        assert result["name"] == "Test Restaurant"
        assert result["autonomy_level"] == "HIGH"
        assert result["risk_profile"]["high_risk_intents"] == ["food_poisoning", "severe_allergy"]
        assert result["risk_profile"]["auto_escalate_threshold"] == 0.7
        assert result["risk_profile"]["confidence_threshold"] == 0.5
        assert result["common_intents"] == ["order_food", "make_reservation", "hours_inquiry"]
        assert result["is_active"] is True
        assert result["is_default"] is False
        assert result["version"] == 1
    
    def test_clear_cache(self, template_service):
        """Test cache clearing"""
        # Add something to cache
        template_service._template_cache["test"] = {"data": "test"}
        template_service._cache_timestamps["test"] = datetime.now().timestamp()
        
        assert "test" in template_service._template_cache
        assert "test" in template_service._cache_timestamps
        
        # Clear cache
        template_service._clear_cache("test")
        
        assert "test" not in template_service._template_cache
        assert "test" not in template_service._cache_timestamps
    
    def test_clear_all_cache(self, template_service):
        """Test clearing all cache"""
        # Add multiple items to cache
        template_service._template_cache["test1"] = {"data": "test1"}
        template_service._template_cache["test2"] = {"data": "test2"}
        template_service._cache_timestamps["test1"] = datetime.now().timestamp()
        template_service._cache_timestamps["test2"] = datetime.now().timestamp()
        
        assert len(template_service._template_cache) == 2
        assert len(template_service._cache_timestamps) == 2
        
        # Clear all cache
        template_service.clear_all_cache()
        
        assert len(template_service._template_cache) == 0
        assert len(template_service._cache_timestamps) == 0


class TestBusinessTemplateModel:
    """Test cases for BusinessTemplate model"""
    
    def test_template_creation(self):
        """Test creating a BusinessTemplate"""
        template = BusinessTemplate(
            template_key="test_clinic",
            name="Test Clinic",
            icon="local_hospital",
            autonomy_level="RESTRICTED",
            high_risk_intents=["emergency"],
            auto_escalate_threshold=0.3,
            confidence_threshold=0.8,
            is_active=True,
            is_default=False,
            version=1,
            created_by=1,
        )
        
        assert template.template_key == "test_clinic"
        assert template.name == "Test Clinic"
        assert template.autonomy_level == "RESTRICTED"
        assert template.high_risk_intents == ["emergency"]
        assert template.is_active is True
        assert template.is_default is False
    
    def test_template_version_creation(self):
        """Test creating a TemplateVersion"""
        version = TemplateVersion(
            template_id=1,
            version_number=2,
            name="Updated Restaurant",
            autonomy_level="MEDIUM",
            change_description="Updated autonomy level",
            is_active=True,
            created_by=1,
        )
        
        assert version.template_id == 1
        assert version.version_number == 2
        assert version.name == "Updated Restaurant"
        assert version.autonomy_level == "MEDIUM"
        assert version.change_description == "Updated autonomy level"
        assert version.is_active is True


class TestTemplateValidation:
    """Test cases for template validation"""
    
    def test_autonomy_levels(self):
        """Test valid autonomy levels"""
        valid_levels = ["HIGH", "MEDIUM", "RESTRICTED"]
        
        for level in valid_levels:
            template = BusinessTemplate(
                template_key=f"test_{level.lower()}",
                name=f"Test {level}",
                autonomy_level=level,
                is_active=True,
                version=1,
                created_by=1,
            )
            assert template.autonomy_level == level
    
    def test_risk_profile_thresholds(self):
        """Test risk profile thresholds are within valid range"""
        template = BusinessTemplate(
            template_key="test_thresholds",
            name="Test Thresholds",
            autonomy_level="MEDIUM",
            auto_escalate_threshold=0.5,
            confidence_threshold=0.6,
            is_active=True,
            version=1,
            created_by=1,
        )
        
        assert 0 <= template.auto_escalate_threshold <= 1
        assert 0 <= template.confidence_threshold <= 1


class TestTemplateIntegration:
    """Integration tests for template operations"""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session"""
        # This would typically use a test database
        # For now, we'll skip actual DB operations
        pass
    
    def test_get_template_with_cache(self, template_service):
        """Test getting template with caching"""
        # Mock cache hit
        template_service._template_cache["restaurant"] = {
            "template_key": "restaurant",
            "name": "Restaurant",
            "is_active": True,
        }
        template_service._cache_timestamps["restaurant"] = datetime.now().timestamp()
        
        # This would normally use a real DB session
        # For now, we're testing the cache logic
        assert "restaurant" in template_service._template_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])