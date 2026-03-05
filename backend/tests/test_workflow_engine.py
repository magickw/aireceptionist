"""
Unit tests for the Workflow Engine.

Tests cover:
- test_simple_workflow: two steps, both succeed
- test_workflow_with_variables: step 1 output used in step 2 input via ${var}
- test_workflow_rollback: step 2 fails, compensation called on step 1
- test_workflow_skip_condition: step with condition that evaluates to true is skipped
- test_workflow_optional_step_failure: non-required step fails, workflow continues
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.workflow_engine import (
    WorkflowExecution,
    WorkflowDefinition,
    WorkflowStep,
    StepStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_definition(steps, name="test_workflow", description="Test workflow"):
    """Create a WorkflowDefinition with the given steps."""
    return WorkflowDefinition(name=name, description=description, steps=steps)


# ---------------------------------------------------------------------------
# test_simple_workflow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_simple_workflow():
    """Two steps, both succeed, workflow returns success."""

    step1 = WorkflowStep(
        name="check_availability",
        tool_name="checkAvailability",
        input_template={"date": "2026-03-10", "time": "09:00"},
        output_variable="availability",
    )
    step2 = WorkflowStep(
        name="book_appointment",
        tool_name="bookAppointment",
        input_template={"date": "2026-03-10", "time": "09:00"},
        output_variable="booking",
    )

    definition = _make_definition([step1, step2])

    executor = AsyncMock(side_effect=[
        {"success": True, "available": True},
        {"success": True, "appointment_id": "apt-123"},
    ])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=executor,
        business_id=1,
    )

    result = await workflow.execute()

    assert result["success"] is True
    assert result["workflow"] == "test_workflow"
    assert "check_availability" in result["results"]
    assert "book_appointment" in result["results"]
    assert executor.call_count == 2

    # Verify both steps are marked COMPLETED
    assert step1.status == StepStatus.COMPLETED
    assert step2.status == StepStatus.COMPLETED


# ---------------------------------------------------------------------------
# test_workflow_with_variables
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_with_variables():
    """Step 1 output should be resolvable as ${variable} in step 2 input."""

    step1 = WorkflowStep(
        name="check_availability",
        tool_name="checkAvailability",
        input_template={"date": "2026-03-10"},
        output_variable="avail_result",
    )
    step2 = WorkflowStep(
        name="book_appointment",
        tool_name="bookAppointment",
        input_template={
            "slot_id": "${avail_result.slot_id}",
            "provider": "${avail_result.provider}",
        },
        output_variable="booking",
    )

    definition = _make_definition([step1, step2])

    executor = AsyncMock(side_effect=[
        {"success": True, "slot_id": "slot-42", "provider": "Dr. Smith"},
        {"success": True, "appointment_id": "apt-999"},
    ])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=executor,
        business_id=1,
    )

    result = await workflow.execute()

    assert result["success"] is True

    # Verify step 2 was called with the resolved variables from step 1
    second_call_args = executor.call_args_list[1]
    tool_input = second_call_args[0][1]  # (tool_name, tool_input, business_id, context)
    assert tool_input["slot_id"] == "slot-42"
    assert tool_input["provider"] == "Dr. Smith"


# ---------------------------------------------------------------------------
# test_workflow_rollback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_rollback():
    """When a required step fails, compensation should be called on completed steps."""

    compensation_executor_calls = []

    async def mock_executor(tool_name, tool_input, business_id, context):
        compensation_executor_calls.append(tool_name)
        if tool_name == "bookAppointment":
            return {"success": False, "message": "No slots available"}
        if tool_name == "cancelReservation":
            return {"success": True}
        return {"success": True, "reservation_id": "res-100"}

    step1 = WorkflowStep(
        name="reserve_slot",
        tool_name="reserveSlot",
        input_template={"date": "2026-03-10"},
        output_variable="reservation",
        compensation_action="cancelReservation",
        compensation_input_template={"reservation_id": "${reservation.reservation_id}"},
    )
    step2 = WorkflowStep(
        name="book_appointment",
        tool_name="bookAppointment",
        input_template={"reservation": "${reservation.reservation_id}"},
        required=True,
    )

    definition = _make_definition([step1, step2])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=mock_executor,
        business_id=1,
    )

    result = await workflow.execute()

    assert result["success"] is False
    assert result["failed_at"] == "book_appointment"
    assert result["rolled_back"] is True

    # Compensation action should have been called
    assert "cancelReservation" in compensation_executor_calls


# ---------------------------------------------------------------------------
# test_workflow_rollback_on_exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_rollback_on_exception():
    """When a required step raises an exception, rollback should occur."""

    rollback_called = []

    async def mock_executor(tool_name, tool_input, business_id, context):
        if tool_name == "failStep":
            raise RuntimeError("External service unavailable")
        if tool_name == "undoStep":
            rollback_called.append(tool_name)
            return {"success": True}
        return {"success": True, "data": "ok"}

    step1 = WorkflowStep(
        name="prepare",
        tool_name="prepareStep",
        input_template={},
        compensation_action="undoStep",
        compensation_input_template={},
    )
    step2 = WorkflowStep(
        name="fail_step",
        tool_name="failStep",
        input_template={},
        required=True,
    )

    definition = _make_definition([step1, step2])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=mock_executor,
        business_id=1,
    )

    result = await workflow.execute()

    assert result["success"] is False
    assert result["failed_at"] == "fail_step"
    assert "External service unavailable" in result["error"]
    assert result["rolled_back"] is True
    assert "undoStep" in rollback_called


# ---------------------------------------------------------------------------
# test_workflow_skip_condition
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_skip_condition():
    """A step whose condition evaluates to true should be skipped."""

    step1 = WorkflowStep(
        name="check_promo",
        tool_name="checkPromo",
        input_template={},
        output_variable="promo_result",
    )
    step2 = WorkflowStep(
        name="apply_discount",
        tool_name="applyDiscount",
        input_template={"discount": "10%"},
        # This condition resolves to "${promo_result.eligible}" => "false"
        # "false == false" => True => step is SKIPPED
        condition="${promo_result.eligible} == false",
    )
    step3 = WorkflowStep(
        name="confirm_booking",
        tool_name="confirmBooking",
        input_template={},
    )

    definition = _make_definition([step1, step2, step3])

    executor = AsyncMock(side_effect=[
        {"success": True, "eligible": "false"},  # step1: promo not eligible
        {"success": True, "confirmed": True},     # step3: confirm
    ])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=executor,
        business_id=1,
    )

    result = await workflow.execute()

    assert result["success"] is True
    assert step2.status == StepStatus.SKIPPED
    # The executor should have been called only twice (step1 + step3, not step2)
    assert executor.call_count == 2


# ---------------------------------------------------------------------------
# test_workflow_optional_step_failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_optional_step_failure():
    """A non-required (optional) step that fails should not stop the workflow."""

    step1 = WorkflowStep(
        name="book_appointment",
        tool_name="bookAppointment",
        input_template={"date": "2026-03-10"},
        output_variable="booking",
    )
    step2 = WorkflowStep(
        name="send_sms_confirmation",
        tool_name="sendSMS",
        input_template={"message": "Your appointment is booked!"},
        required=False,  # Optional step
    )
    step3 = WorkflowStep(
        name="update_calendar",
        tool_name="updateCalendar",
        input_template={"event": "appointment"},
    )

    definition = _make_definition([step1, step2, step3])

    async def mock_executor(tool_name, tool_input, business_id, context):
        if tool_name == "sendSMS":
            raise ConnectionError("SMS gateway unreachable")
        return {"success": True}

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=mock_executor,
        business_id=1,
    )

    result = await workflow.execute()

    # Workflow should still succeed overall
    assert result["success"] is True
    # Step 2 should be marked as FAILED
    assert step2.status == StepStatus.FAILED
    assert step2.error == "SMS gateway unreachable"
    # Step 3 should still have run
    assert step3.status == StepStatus.COMPLETED


# ---------------------------------------------------------------------------
# test_workflow_optional_step_returns_failure_dict
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_optional_step_returns_failure_dict():
    """An optional step that returns {success: False} should not halt the workflow."""

    step1 = WorkflowStep(
        name="main_action",
        tool_name="mainAction",
        input_template={},
    )
    step2 = WorkflowStep(
        name="optional_notification",
        tool_name="notify",
        input_template={},
        required=False,
    )

    definition = _make_definition([step1, step2])

    executor = AsyncMock(side_effect=[
        {"success": True, "data": "ok"},
        {"success": False, "message": "Notification service down"},
    ])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=executor,
        business_id=1,
    )

    result = await workflow.execute()

    # Workflow should succeed because the failing step is optional
    assert result["success"] is True


# ---------------------------------------------------------------------------
# test_progress_callback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_progress_callback():
    """Progress callback should be invoked at each step transition."""

    progress_messages = []

    async def capture_progress(message):
        progress_messages.append(message)

    step1 = WorkflowStep(
        name="step_one",
        tool_name="doSomething",
        input_template={},
    )

    definition = _make_definition([step1])

    executor = AsyncMock(return_value={"success": True})

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=executor,
        business_id=1,
        progress_callback=capture_progress,
    )

    await workflow.execute()

    # Should have starting message, running message, completed message, and final message
    assert any("Starting workflow" in msg for msg in progress_messages)
    assert any("Running" in msg for msg in progress_messages)
    assert any("Completed" in msg or "completed" in msg for msg in progress_messages)


# ---------------------------------------------------------------------------
# test_variable_resolution_dot_notation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_variable_resolution_dot_notation():
    """Nested dot notation in variables should resolve correctly."""

    step1 = WorkflowStep(
        name="get_data",
        tool_name="getData",
        input_template={},
        output_variable="api_result",
    )
    step2 = WorkflowStep(
        name="use_data",
        tool_name="useData",
        input_template={
            "id": "${api_result.nested.deep_id}",
        },
    )

    definition = _make_definition([step1, step2])

    executor = AsyncMock(side_effect=[
        {"nested": {"deep_id": "deep-val-42"}},
        {"success": True},
    ])

    workflow = WorkflowExecution(
        definition=definition,
        action_executor=executor,
        business_id=1,
    )

    result = await workflow.execute()
    assert result["success"] is True

    # Verify the resolved input
    second_call_input = executor.call_args_list[1][0][1]
    assert second_call_input["id"] == "deep-val-42"
