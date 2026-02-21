"""Unit tests for Nova Act Automation Service (Playwright)"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import asyncio
import json

from app.services.nova_act import (
    NovaActAutomation,
    AutomationAction,
    AutomationStatus,
    AutomationStep,
    AutomationWorkflow
)


@pytest.fixture
def automation_service():
    """Create a NovaActAutomation instance"""
    return NovaActAutomation()


@pytest.fixture
def sample_step():
    """Sample automation step"""
    return AutomationStep(
        step_id=1,
        action=AutomationAction.NAVIGATE,
        description="Navigate to test page",
        target="https://example.com",
        wait_ms=1000
    )


@pytest.fixture
def sample_workflow():
    """Sample automation workflow"""
    steps = [
        AutomationStep(
            step_id=1,
            action=AutomationAction.NAVIGATE,
            description="Navigate to page",
            target="https://example.com"
        ),
        AutomationStep(
            step_id=2,
            action=AutomationAction.CLICK,
            description="Click button",
            selector="#submit"
        )
    ]
    
    return AutomationWorkflow(
        workflow_id="test-workflow-1",
        name="Test Workflow",
        description="A test automation workflow",
        steps=steps
    )


class TestAutomationStep:
    """Test cases for AutomationStep"""
    
    def test_step_creation(self):
        """Test creating an automation step"""
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.NAVIGATE,
            description="Navigate to page",
            target="https://example.com"
        )
        
        assert step.step_id == 1
        assert step.action == AutomationAction.NAVIGATE
        assert step.status == AutomationStatus.PENDING
        assert step.result is None
    
    def test_step_to_dict(self, sample_step):
        """Test converting step to dictionary"""
        step_dict = sample_step.to_dict()
        
        assert step_dict["step_id"] == 1
        assert step_dict["action"] == "navigate"
        assert step_dict["status"] == "pending"
        assert "target" in step_dict
    
    def test_all_action_types(self):
        """Test all automation action types"""
        actions = [
            AutomationAction.NAVIGATE,
            AutomationAction.CLICK,
            AutomationAction.TYPE,
            AutomationAction.SELECT,
            AutomationAction.WAIT,
            AutomationAction.SCROLL,
            AutomationAction.EXTRACT,
            AutomationAction.VERIFY,
            AutomationAction.SUBMIT
        ]
        
        for action in actions:
            step = AutomationStep(
                step_id=1,
                action=action,
                description="Test action"
            )
            assert step.action == action


class TestAutomationWorkflow:
    """Test cases for AutomationWorkflow"""
    
    def test_workflow_creation(self, sample_workflow):
        """Test creating a workflow"""
        assert sample_workflow.workflow_id == "test-workflow-1"
        assert sample_workflow.name == "Test Workflow"
        assert len(sample_workflow.steps) == 2
        assert sample_workflow.status == AutomationStatus.PENDING
    
    def test_workflow_to_dict(self, sample_workflow):
        """Test converting workflow to dictionary"""
        workflow_dict = sample_workflow.to_dict()
        
        assert workflow_dict["workflow_id"] == "test-workflow-1"
        assert workflow_dict["name"] == "Test Workflow"
        assert workflow_dict["total_steps"] == 2
        assert workflow_dict["current_step"] == 0
        assert "steps" in workflow_dict
    
    def test_workflow_progress_percent(self, sample_workflow):
        """Test workflow progress calculation"""
        sample_workflow.current_step = 1
        workflow_dict = sample_workflow.to_dict()
        
        assert workflow_dict["progress_percent"] == 50


class TestPlaywrightBrowserManagement:
    """Test cases for Playwright browser management"""
    
    @pytest.mark.asyncio
    async def test_get_page_for_workflow(self, automation_service):
        """Test getting a page for a workflow"""
        # Mock Playwright
        mock_playwright = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch('app.services.nova_act.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            page = await automation_service._get_page_for_workflow({"workflow_id": "test-1"})
            
            assert page is not None
            assert "test-1" in automation_service._pages
    
    @pytest.mark.asyncio
    async def test_close_browser_for_workflow(self, automation_service):
        """Test closing browser for a workflow"""
        # Mock page
        mock_page = Mock()
        mock_page.close = AsyncMock()
        mock_browser = Mock()
        mock_browser.close = AsyncMock()
        
        automation_service._pages["test-1"] = mock_page
        automation_service._browsers["test-1"] = mock_browser
        
        await automation_service._close_browser_for_workflow("test-1")
        
        assert "test-1" not in automation_service._pages
        assert "test-1" not in automation_service._browsers
    
    @pytest.mark.asyncio
    async def test_cleanup_all_browsers(self, automation_service):
        """Test cleaning up all browsers"""
        # Mock pages and browsers
        mock_page1 = Mock()
        mock_page1.close = AsyncMock()
        mock_page2 = Mock()
        mock_page2.close = AsyncMock()
        
        mock_browser1 = Mock()
        mock_browser1.close = AsyncMock()
        mock_browser2 = Mock()
        mock_browser2.close = AsyncMock()
        
        automation_service._pages = {"test-1": mock_page1, "test-2": mock_page2}
        automation_service._browsers = {"test-1": mock_browser1, "test-2": mock_browser2}
        
        await automation_service.cleanup_all_browsers()
        
        assert len(automation_service._pages) == 0
        assert len(automation_service._browsers) == 0


class TestPlaywrightActionExecutors:
    """Test cases for Playwright action execution"""
    
    @pytest.mark.asyncio
    async def test_execute_navigate(self, automation_service):
        """Test executing navigate action"""
        mock_page = Mock()
        mock_page.goto = AsyncMock()
        mock_page.url = "https://example.com"
        
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.NAVIGATE,
            description="Navigate to page",
            target="https://example.com"
        )
        
        result = await automation_service._execute_navigate(mock_page, step)
        
        assert result["loaded"] is True
        assert result["url"] == "https://example.com"
        mock_page.goto.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_click(self, automation_service):
        """Test executing click action"""
        mock_page = Mock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.click = AsyncMock()
        
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.CLICK,
            description="Click button",
            selector="#submit"
        )
        
        result = await automation_service._execute_click(mock_page, step)
        
        assert result["clicked"] is True
        assert result["selector"] == "#submit"
        mock_page.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_type(self, automation_service):
        """Test executing type action"""
        mock_page = Mock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.type = AsyncMock()
        
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.TYPE,
            description="Type in field",
            selector="#name",
            value="John Doe"
        )
        
        result = await automation_service._execute_type(mock_page, step)
        
        assert result["typed"] is True
        assert result["value_length"] == 8
        mock_page.fill.assert_called_once()
        mock_page.type.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_wait(self, automation_service):
        """Test executing wait action"""
        mock_page = Mock()
        mock_page.wait_for_selector = AsyncMock()
        
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.WAIT,
            description="Wait for element",
            selector="#loading",
            wait_ms=1000
        )
        
        result = await automation_service._execute_wait(mock_page, step)
        
        assert result["waited_for"] == "element"
        assert result["selector"] == "#loading"
    
    @pytest.mark.asyncio
    async def test_execute_verify(self, automation_service):
        """Test executing verify action"""
        mock_page = Mock()
        mock_page.query_selector = Mock(return_value=True)
        
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.VERIFY,
            description="Verify element exists",
            selector="#success",
            verification="element exists"
        )
        
        result = await automation_service._execute_verify(mock_page, step)
        
        assert result["verified"] is True
        assert result["found"] is True
    
    @pytest.mark.asyncio
    async def test_execute_extract(self, automation_service):
        """Test executing extract action"""
        mock_element = Mock()
        mock_element.text_content = AsyncMock(return_value="Extracted text")
        mock_page = Mock()
        mock_page.query_selector = Mock(return_value=mock_element)
        
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.EXTRACT,
            description="Extract text",
            selector="#content"
        )
        
        result = await automation_service._execute_extract(mock_page, step)
        
        assert "text" in result
        assert result["text"] == "Extracted text"


class TestWorkflowExecution:
    """Test cases for workflow execution"""
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, automation_service, sample_workflow):
        """Test successful workflow execution"""
        # Mock page
        mock_page = Mock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.url = "https://example.com"
        
        with patch.object(automation_service, '_get_page_for_workflow', AsyncMock(return_value=mock_page)), \
             patch.object(automation_service, '_close_browser_for_workflow', AsyncMock()):
            
            events = []
            async for event in automation_service.execute_workflow(sample_workflow):
                events.append(event)
            
            # Check that we got expected events
            assert any(e["type"] == "workflow_started" for e in events)
            assert any(e["type"] == "step_started" for e in events)
            assert any(e["type"] == "step_completed" for e in events)
            assert any(e["type"] == "workflow_completed" for e in events)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_cleanup(self, automation_service, sample_workflow):
        """Test that workflow cleanup happens on completion"""
        mock_page = Mock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.url = "https://example.com"
        
        with patch.object(automation_service, '_get_page_for_workflow', AsyncMock(return_value=mock_page)), \
             patch.object(automation_service, '_close_browser_for_workflow', AsyncMock()) as mock_close:
            
            async for _ in automation_service.execute_workflow(sample_workflow):
                pass
            
            # Verify cleanup was called
            mock_close.assert_called_once_with(sample_workflow.workflow_id)


class TestWorkflowCreation:
    """Test cases for workflow creation methods"""
    
    def test_create_calendly_booking_workflow(self, automation_service):
        """Test creating Calendly booking workflow"""
        workflow = automation_service.create_calendly_booking_workflow(
            customer_name="John Doe",
            customer_phone="555-1234",
            customer_email="john@example.com",
            service="Consultation",
            date="2024-01-15",
            time="2:00 PM",
            calendly_url="https://calendly.com/example"
        )
        
        assert workflow.name == "Calendly Booking"
        assert "John Doe" in workflow.description
        assert len(workflow.steps) == 9  # Should have 9 steps
        assert workflow.steps[0].action == AutomationAction.NAVIGATE
        assert workflow.steps[-1].action == AutomationAction.VERIFY
    
    def test_create_crm_update_workflow_salesforce(self, automation_service):
        """Test creating Salesforce CRM update workflow"""
        workflow = automation_service.create_crm_update_workflow(
            crm_type="salesforce",
            customer_data={"name": "John Doe", "phone": "555-1234"},
            interaction_data={"type": "call"}
        )
        
        assert workflow.name == "Salesforce CRM Update"
        assert len(workflow.steps) == 5
        assert workflow.steps[0].action == AutomationAction.NAVIGATE
        assert workflow.steps[-1].action == AutomationAction.SUBMIT
    
    def test_create_crm_update_workflow_hubspot(self, automation_service):
        """Test creating HubSpot CRM update workflow"""
        workflow = automation_service.create_crm_update_workflow(
            crm_type="hubspot",
            customer_data={"name": "Jane Doe", "email": "jane@example.com"},
            interaction_data={"type": "email"}
        )
        
        assert workflow.name == "Hubspot CRM Update"  # Lowercase 'p' in actual implementation
        assert len(workflow.steps) == 5
        assert workflow.steps[0].action == AutomationAction.NAVIGATE


class TestWorkflowStatus:
    """Test cases for workflow status management"""
    
    def test_get_workflow_status(self, automation_service, sample_workflow):
        """Test getting workflow status"""
        automation_service.active_workflows[sample_workflow.workflow_id] = sample_workflow
        sample_workflow.status = AutomationStatus.IN_PROGRESS
        sample_workflow.current_step = 1
        
        status = automation_service.get_workflow_status(sample_workflow.workflow_id)
        
        assert status is not None
        assert status["status"] == "in_progress"
        assert status["current_step"] == 1
    
    def test_get_workflow_status_not_found(self, automation_service):
        """Test getting status for non-existent workflow"""
        status = automation_service.get_workflow_status("non-existent")
        
        assert status is None
    
    def test_cancel_workflow(self, automation_service, sample_workflow):
        """Test canceling a workflow"""
        automation_service.active_workflows[sample_workflow.workflow_id] = sample_workflow
        
        result = automation_service.cancel_workflow(sample_workflow.workflow_id)
        
        assert result is True
        assert sample_workflow.status == AutomationStatus.CANCELLED
    
    def test_cancel_workflow_not_found(self, automation_service):
        """Test canceling non-existent workflow"""
        result = automation_service.cancel_workflow("non-existent")
        
        assert result is False


class TestStepObservation:
    """Test cases for step observation generation"""
    
    def test_generate_step_observation_navigate(self, automation_service):
        """Test observation for navigate action"""
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.NAVIGATE,
            description="Navigate to page",
            target="https://example.com"
        )
        
        observation = automation_service._generate_step_observation(step)
        
        assert "Navigating to" in observation
        assert "https://example.com" in observation
    
    def test_generate_step_observation_type_masked(self, automation_service):
        """Test observation for type action with sensitive data"""
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.TYPE,
            description="Enter password",
            target="#password",
            value="secret123"
        )
        
        observation = automation_service._generate_step_observation(step)
        
        assert "Typing" in observation
        assert "***" in observation  # Should be masked
        assert "secret123" not in observation  # Should not contain actual value


class TestNovaObservation:
    """Test cases for Nova multimodal observation"""
    
    @pytest.mark.asyncio
    async def test_observe_with_nova_and_screenshot(self, automation_service):
        """Test Nova observation with screenshot"""
        step = AutomationStep(
            step_id=1,
            action=AutomationAction.NAVIGATE,
            description="Navigate to page"
        )
        
        with patch.object(automation_service, 'bedrock_runtime') as mock_runtime:
            mock_response = Mock()
            mock_response_body = Mock()
            mock_response_body.read.return_value.decode.return_value = json.dumps({
                "messages": [{"content": [{"text": "Page loaded successfully"}] }]
            })
            mock_response = {"body": mock_response_body}
            mock_runtime.invoke_model.return_value = mock_response
            
            observation = await automation_service._observe_with_nova_and_screenshot(
                step, b"fake_screenshot"
            )
            
            assert isinstance(observation, str)
            assert len(observation) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])