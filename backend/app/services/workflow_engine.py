"""
Workflow Engine - Multi-step tool orchestration with variable resolution and rollback.
"""
import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from app.core.logging import get_logger

logger = get_logger("workflow_engine")


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    tool_name: str
    input_template: Dict[str, Any]  # Can contain ${variable} references
    output_variable: str = ""  # Variable name to store result
    condition: str = ""  # Skip condition expression (e.g., "${available} == false")
    compensation_action: str = ""  # Tool name to call on rollback
    compensation_input_template: Dict[str, Any] = field(default_factory=dict)
    required: bool = True
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """Defines a complete workflow."""
    name: str
    description: str
    steps: List[WorkflowStep]


class WorkflowExecution:
    """
    Executes a workflow definition step by step.
    Handles variable resolution, condition evaluation, and rollback.
    """

    def __init__(
        self,
        definition: WorkflowDefinition,
        action_executor: Callable,  # async (tool_name, tool_input, business_id, context) -> result
        business_id: int,
        context: Dict[str, Any] = None,
        progress_callback: Optional[Callable] = None,  # async (message) -> None
    ):
        self.definition = definition
        self.action_executor = action_executor
        self.business_id = business_id
        self.context = context or {}
        self.progress_callback = progress_callback
        self.variables: Dict[str, Any] = {}
        self.completed_steps: List[WorkflowStep] = []

    def _resolve_variables(self, template: Any) -> Any:
        """Resolve ${variable} references in templates."""
        if isinstance(template, str):
            def replace_var(match):
                var_name = match.group(1)
                # Support dot notation: ${result.appointment_id}
                parts = var_name.split(".")
                val = self.variables
                for part in parts:
                    if isinstance(val, dict):
                        val = val.get(part, "")
                    else:
                        return match.group(0)
                return str(val) if not isinstance(val, str) else val
            return re.sub(r'\$\{([^}]+)\}', replace_var, template)
        elif isinstance(template, dict):
            return {k: self._resolve_variables(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._resolve_variables(item) for item in template]
        return template

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a simple condition expression. Returns True if step should be SKIPPED."""
        if not condition:
            return False
        resolved = self._resolve_variables(condition)
        # Simple equality checks: "value == false", "value == true"
        if "==" in resolved:
            left, right = [s.strip() for s in resolved.split("==", 1)]
            return str(left).lower() == str(right).lower()
        if "!=" in resolved:
            left, right = [s.strip() for s in resolved.split("!=", 1)]
            return str(left).lower() != str(right).lower()
        return False

    async def _report_progress(self, message: str):
        if self.progress_callback:
            try:
                await self.progress_callback(message)
            except Exception:
                pass

    async def execute(self) -> Dict[str, Any]:
        """Execute all steps in the workflow sequentially."""
        logger.info(f"Starting workflow: {self.definition.name}")
        await self._report_progress(f"Starting workflow: {self.definition.name}")

        results = {}

        for i, step in enumerate(self.definition.steps):
            step_num = i + 1
            total = len(self.definition.steps)

            # Check skip condition
            if step.condition and self._evaluate_condition(step.condition):
                step.status = StepStatus.SKIPPED
                await self._report_progress(f"Step {step_num}/{total}: {step.name} - Skipped (condition met)")
                logger.info(f"Skipping step {step.name}: condition met")
                continue

            # Resolve variables in input template
            resolved_input = self._resolve_variables(step.input_template)

            step.status = StepStatus.RUNNING
            await self._report_progress(f"Step {step_num}/{total}: {step.name} - Running...")

            try:
                result = await self.action_executor(
                    step.tool_name, resolved_input, self.business_id, self.context
                )

                step.result = result
                step.status = StepStatus.COMPLETED
                self.completed_steps.append(step)

                # Store output variable
                if step.output_variable:
                    self.variables[step.output_variable] = result

                results[step.name] = result

                # Check if step failed
                if isinstance(result, dict) and not result.get("success", True):
                    if step.required:
                        step.status = StepStatus.FAILED
                        step.error = result.get("message", "Step failed")
                        await self._report_progress(f"Step {step_num}/{total}: {step.name} - Failed: {step.error}")
                        logger.error(f"Required step {step.name} failed: {step.error}")
                        # Trigger rollback
                        await self._rollback()
                        return {
                            "success": False,
                            "workflow": self.definition.name,
                            "failed_at": step.name,
                            "error": step.error,
                            "results": results,
                            "rolled_back": True,
                        }

                await self._report_progress(f"Step {step_num}/{total}: {step.name} - Completed")
                logger.info(f"Step {step.name} completed successfully")

            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                logger.error(f"Step {step.name} raised exception: {e}")

                if step.required:
                    await self._rollback()
                    return {
                        "success": False,
                        "workflow": self.definition.name,
                        "failed_at": step.name,
                        "error": str(e),
                        "results": results,
                        "rolled_back": True,
                    }

        await self._report_progress(f"Workflow {self.definition.name} completed successfully!")
        return {
            "success": True,
            "workflow": self.definition.name,
            "results": results,
        }

    async def _rollback(self):
        """Roll back completed steps in reverse order."""
        logger.info(f"Rolling back workflow: {self.definition.name}")
        await self._report_progress("Rolling back previous steps...")

        for step in reversed(self.completed_steps):
            if step.compensation_action:
                try:
                    comp_input = self._resolve_variables(step.compensation_input_template)
                    await self.action_executor(
                        step.compensation_action, comp_input, self.business_id, self.context
                    )
                    step.status = StepStatus.COMPENSATED
                    logger.info(f"Compensated step: {step.name}")
                except Exception as e:
                    logger.error(f"Compensation failed for step {step.name}: {e}")
