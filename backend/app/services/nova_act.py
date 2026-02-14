"""
Nova Act UI Automation Service
Autonomous Business Operations Agent - Automation Layer
"""
import boto3
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum
from app.core.config import settings


class AutomationAction(Enum):
    """Types of automation actions"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    WAIT = "wait"
    SCROLL = "scroll"
    EXTRACT = "extract"
    VERIFY = "verify"
    SUBMIT = "submit"


class AutomationStatus(Enum):
    """Status of automation execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutomationStep:
    """Represents a single automation step"""
    
    def __init__(
        self,
        step_id: int,
        action: AutomationAction,
        description: str,
        target: Optional[str] = None,
        value: Optional[str] = None,
        selector: Optional[str] = None,
        wait_ms: Optional[int] = None,
        verification: Optional[str] = None
    ):
        self.step_id = step_id
        self.action = action
        self.description = description
        self.target = target  # URL for navigate, element selector for other actions
        self.value = value  # Text to type or value to select
        self.selector = selector  # CSS selector for element
        self.wait_ms = wait_ms  # Time to wait after action
        self.verification = verification  # Expected result to verify
        
        self.status = AutomationStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.screenshot: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "step_id": self.step_id,
            "action": self.action.value,
            "description": self.description,
            "target": self.target,
            "value": self.value,
            "selector": self.selector,
            "wait_ms": self.wait_ms,
            "verification": self.verification,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class AutomationWorkflow:
    """Represents a complete automation workflow"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        steps: List[AutomationStep],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps
        self.metadata = metadata or {}
        
        self.status = AutomationStatus.PENDING
        self.current_step = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "progress_percent": int((self.current_step / len(self.steps)) * 100) if self.steps else 0,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class NovaActAutomation:
    """
    Nova Act-powered UI automation service.
    
    Handles autonomous execution of workflows in external applications:
    - Calendly booking
    - CRM updates (Salesforce, HubSpot)
    - Form submissions
    - Data extraction
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-act-v1:0"
        
        # Active workflows
        self.active_workflows: Dict[str, AutomationWorkflow] = {}
    
    async def execute_workflow(
        self,
        workflow: AutomationWorkflow,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute an automation workflow with real-time progress updates.
        
        Args:
            workflow: The workflow to execute
            context: Additional context (customer info, business settings, etc.)
            
        Yields:
            Progress updates with current step status
        """
        try:
            self.active_workflows[workflow.workflow_id] = workflow
            workflow.status = AutomationStatus.IN_PROGRESS
            workflow.started_at = datetime.now()
            
            yield {
                "type": "workflow_started",
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "total_steps": len(workflow.steps)
            }
            
            # Execute each step
            for i, step in enumerate(workflow.steps):
                workflow.current_step = i
                
                # Generate detailed step observation for UI
                observation = self._generate_step_observation(step)
                
                yield {
                    "type": "step_started",
                    "workflow_id": workflow.workflow_id,
                    "step_id": step.step_id,
                    "description": step.description,
                    "action": step.action.value if hasattr(step.action, 'value') else str(step.action),
                    "target": step.target,
                    "value": step.value,
                    "observation": observation
                }
                
                # Execute the step
                result = await self._execute_step(step, context)
                
                if result["success"]:
                    step.status = AutomationStatus.COMPLETED
                    step.result = result["data"]
                    step.completed_at = datetime.now()
                    
                    yield {
                        "type": "step_completed",
                        "workflow_id": workflow.workflow_id,
                        "step_id": step.step_id,
                        "result": result["data"],
                        "progress_percent": int(((i + 1) / len(workflow.steps)) * 100)
                    }
                else:
                    step.status = AutomationStatus.FAILED
                    step.error = result["error"]
                    
                    workflow.status = AutomationStatus.FAILED
                    workflow.error = result["error"]
                    workflow.completed_at = datetime.now()
                    
                    yield {
                        "type": "step_failed",
                        "workflow_id": workflow.workflow_id,
                        "step_id": step.step_id,
                        "error": result["error"]
                    }
                    
                    # Try fallback if available
                    fallback_result = await self._try_fallback(step, context)
                    if fallback_result["success"]:
                        yield {
                            "type": "fallback_executed",
                            "workflow_id": workflow.workflow_id,
                            "step_id": step.step_id,
                            "fallback_result": fallback_result["data"]
                        }
                    else:
                        # Stop workflow on failure
                        yield {
                            "type": "workflow_failed",
                            "workflow_id": workflow.workflow_id,
                            "error": result["error"]
                        }
                        return
            
            # Workflow completed successfully
            workflow.status = AutomationStatus.COMPLETED
            workflow.completed_at = datetime.now()
            
            yield {
                "type": "workflow_completed",
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "total_steps": len(workflow.steps),
                "duration_seconds": (workflow.completed_at - workflow.started_at).total_seconds()
            }
            
        except Exception as e:
            workflow.status = AutomationStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.now()
            
            yield {
                "type": "workflow_error",
                "workflow_id": workflow.workflow_id,
                "error": str(e)
            }
    
    async def _execute_step(
        self,
        step: AutomationStep,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single automation step.
        
        This is a mock implementation. In production, this would use:
        - Playwright for browser automation
        - API calls for CRM integrations
        - Nova Act for intelligent action execution
        """
        
        step.started_at = datetime.now()
        
        try:
            # Simulate step execution
            await asyncio.sleep(0.5)  # Simulate processing time
            
            # Mock execution based on action type
            if step.action == AutomationAction.NAVIGATE:
                result = {"url": step.target, "loaded": True}
            elif step.action == AutomationAction.CLICK:
                result = {"clicked": True, "element": step.selector}
            elif step.action == AutomationAction.TYPE:
                result = {"typed": True, "value": step.value, "field": step.selector}
            elif step.action == AutomationAction.SELECT:
                result = {"selected": True, "value": step.value, "dropdown": step.selector}
            elif step.action == AutomationAction.WAIT:
                await asyncio.sleep((step.wait_ms or 1000) / 1000)
                result = {"waited_ms": step.wait_ms}
            elif step.action == AutomationAction.SUBMIT:
                result = {"submitted": True, "form": step.selector}
            elif step.action == AutomationAction.VERIFY:
                result = {"verified": True, "expected": step.verification, "found": True}
            else:
                result = {"action": step.action.value, "completed": True}
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _try_fallback(
        self,
        step: AutomationStep,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Try alternative approach if step fails.
        """
        # Mock fallback implementation
        await asyncio.sleep(0.3)
        return {
            "success": True,
            "data": {"fallback": True, "action": step.action.value}
        }
    
    async def generate_automation_plan(
        self,
        task: str,
        reasoning_data: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> List[AutomationStep]:
        """
        Use Nova Act to generate an automation plan for a given task.
        
        Args:
            task: Description of the task to automate
            reasoning_data: Result from Nova Lite reasoning
            business_context: Business settings and configuration
            
        Returns:
            List of automation steps
        """
        
        prompt = f"""
You are Nova Act, an autonomous UI automation planner.

Task: {task}

Context:
- Reasoning Result: {json.dumps(reasoning_data, indent=2)}
- Business Context: {json.dumps(business_context, indent=2)}

Generate a step-by-step automation plan to complete this task.
Each step should be one of these actions:
- navigate: Go to a URL
- click: Click an element
- type: Enter text in a field
- select: Select from a dropdown
- wait: Wait for an element
- submit: Submit a form
- verify: Verify a condition

Output format (JSON):
{{
  "steps": [
    {{
      "action": "navigate",
      "description": "Go to Calendly booking page",
      "target": "https://calendly.com/example",
      "selector": null,
      "value": null,
      "wait_ms": 2000
    }},
    {{
      "action": "click",
      "description": "Select service type",
      "target": null,
      "selector": "[data-testid='service-select']",
      "value": null,
      "wait_ms": 500
    }},
    ...
  ]
}}
"""
        
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [{"role": "user", "content": prompt}],
                    "inferenceConfig": {
                        "maxTokens": 2048,
                        "temperature": 0.3
                    }
                })
            )
            
            response_body = json.loads(response["body"].read().decode())
            
            if "messages" in response_body and len(response_body["messages"]) > 0:
                content = response_body["messages"][0]["content"]
                
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}', content)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    plan_data = json.loads(content)
                
                # Convert to AutomationStep objects
                steps = []
                for i, step_data in enumerate(plan_data.get("steps", [])):
                    step = AutomationStep(
                        step_id=i + 1,
                        action=AutomationAction(step_data["action"]),
                        description=step_data["description"],
                        target=step_data.get("target"),
                        value=step_data.get("value"),
                        selector=step_data.get("selector"),
                        wait_ms=step_data.get("wait_ms"),
                        verification=step_data.get("verification")
                    )
                    steps.append(step)
                
                return steps
            
            return []
            
        except Exception as e:
            print(f"Error generating automation plan: {e}")
            return []
    
    def create_calendly_booking_workflow(
        self,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        service: str,
        date: str,
        time: str,
        calendly_url: str
    ) -> AutomationWorkflow:
        """
        Create a workflow for booking via Calendly.
        
        Args:
            customer_name: Customer's name
            customer_phone: Customer's phone number
            customer_email: Customer's email
            service: Service type to book
            date: Preferred date
            time: Preferred time
            calendly_url: Calendly booking URL
            
        Returns:
            AutomationWorkflow object
        """
        
        workflow_id = f"calendly_booking_{datetime.now().timestamp()}"
        
        steps = [
            AutomationStep(
                step_id=1,
                action=AutomationAction.NAVIGATE,
                description=f"Navigate to Calendly booking page",
                target=calendly_url,
                wait_ms=3000
            ),
            AutomationStep(
                step_id=2,
                action=AutomationAction.SELECT,
                description=f"Select service: {service}",
                selector="[data-testid='service-select']",
                value=service,
                wait_ms=500
            ),
            AutomationStep(
                step_id=3,
                action=AutomationAction.CLICK,
                description=f"Select date: {date}",
                selector=f"[data-date='{date}']",
                wait_ms=500
            ),
            AutomationStep(
                step_id=4,
                action=AutomationAction.CLICK,
                description=f"Select time: {time}",
                selector=f"[data-time='{time}']",
                wait_ms=500
            ),
            AutomationStep(
                step_id=5,
                action=AutomationAction.TYPE,
                description="Enter customer name",
                selector="input[name='name']",
                value=customer_name,
                wait_ms=300
            ),
            AutomationStep(
                step_id=6,
                action=AutomationAction.TYPE,
                description="Enter customer email",
                selector="input[name='email']",
                value=customer_email,
                wait_ms=300
            ),
            AutomationStep(
                step_id=7,
                action=AutomationAction.TYPE,
                description="Enter customer phone",
                selector="input[name='phone']",
                value=customer_phone,
                wait_ms=300
            ),
            AutomationStep(
                step_id=8,
                action=AutomationAction.SUBMIT,
                description="Submit booking form",
                selector="button[type='submit']",
                wait_ms=2000
            ),
            AutomationStep(
                step_id=9,
                action=AutomationAction.VERIFY,
                description="Verify booking confirmation",
                verification="booking_confirmed",
                wait_ms=1000
            )
        ]
        
        return AutomationWorkflow(
            workflow_id=workflow_id,
            name="Calendly Booking",
            description=f"Book {service} appointment for {customer_name} on {date} at {time}",
            steps=steps,
            metadata={
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "service": service,
                "date": date,
                "time": time,
                "calendly_url": calendly_url
            }
        )
    
    def create_crm_update_workflow(
        self,
        crm_type: str,
        customer_data: Dict[str, Any],
        interaction_data: Dict[str, Any]
    ) -> AutomationWorkflow:
        """
        Create a workflow for updating CRM records.
        
        Args:
            crm_type: Type of CRM (salesforce, hubspot)
            customer_data: Customer information
            interaction_data: Recent interaction data
            
        Returns:
            AutomationWorkflow object
        """
        
        workflow_id = f"crm_update_{crm_type}_{datetime.now().timestamp()}"
        
        if crm_type == "salesforce":
            steps = [
                AutomationStep(
                    step_id=1,
                    action=AutomationAction.NAVIGATE,
                    description="Navigate to Salesforce",
                    target="https://salesforce.com/lightning/o/Contact/home",
                    wait_ms=2000
                ),
                AutomationStep(
                    step_id=2,
                    action=AutomationAction.CLICK,
                    description="Click New Contact",
                    selector="button[title='New']",
                    wait_ms=1000
                ),
                AutomationStep(
                    step_id=3,
                    action=AutomationAction.TYPE,
                    description="Enter customer name",
                    selector="input[name='firstName']",
                    value=customer_data.get("name", ""),
                    wait_ms=300
                ),
                AutomationStep(
                    step_id=4,
                    action=AutomationAction.TYPE,
                    description="Enter customer phone",
                    selector="input[name='phone']",
                    value=customer_data.get("phone", ""),
                    wait_ms=300
                ),
                AutomationStep(
                    step_id=5,
                    action=AutomationAction.SUBMIT,
                    description="Save contact",
                    selector="button[type='submit']",
                    wait_ms=2000
                )
            ]
        else:  # HubSpot
            steps = [
                AutomationStep(
                    step_id=1,
                    action=AutomationAction.NAVIGATE,
                    description="Navigate to HubSpot",
                    target="https://app.hubspot.com/contacts",
                    wait_ms=2000
                ),
                AutomationStep(
                    step_id=2,
                    action=AutomationAction.CLICK,
                    description="Click Create Contact",
                    selector="[data-testid='create-contact']",
                    wait_ms=1000
                ),
                AutomationStep(
                    step_id=3,
                    action=AutomationAction.TYPE,
                    description="Enter customer name",
                    selector="input[name='firstname']",
                    value=customer_data.get("name", ""),
                    wait_ms=300
                ),
                AutomationStep(
                    step_id=4,
                    action=AutomationAction.TYPE,
                    description="Enter customer email",
                    selector="input[name='email']",
                    value=customer_data.get("email", ""),
                    wait_ms=300
                ),
                AutomationStep(
                    step_id=5,
                    action=AutomationAction.SUBMIT,
                    description="Save contact",
                    selector="button[type='submit']",
                    wait_ms=2000
                )
            ]
        
        return AutomationWorkflow(
            workflow_id=workflow_id,
            name=f"{crm_type.capitalize()} CRM Update",
            description=f"Update {crm_type} with customer interaction data",
            steps=steps,
            metadata={
                "crm_type": crm_type,
                "customer_data": customer_data,
                "interaction_data": interaction_data
            }
        )
    
    def _generate_step_observation(self, step: AutomationStep) -> str:
        """
        Generate a human-readable observation for the current step.
        
        Args:
            step: The automation step being executed
            
        Returns:
            A descriptive observation string for UI display
        """
        action = step.action.value if hasattr(step.action, 'value') else str(step.action)
        observations = []
        
        if action == "navigate":
            observations.append(f"Navigating to {step.target}")
        elif action == "click":
            if step.selector:
                observations.append(f"Clicking element: {step.selector}")
            else:
                observations.append(f"Clicking on {step.target}")
        elif action == "type":
            if step.value:
                # Mask sensitive data
                display_value = step.value
                if any(sensitive in step.target.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                    display_value = "***"
                elif len(step.value) > 4:
                    display_value = step.value[:2] + "***" + step.value[-2:]
                observations.append(f"Typing '{display_value}' into {step.target}")
            else:
                observations.append(f"Typing into {step.target}")
        elif action == "wait":
            observations.append(f"Waiting for {step.wait_ms}ms")
        elif action == "screenshot":
            observations.append("Capturing screenshot for verification")
        elif action == "extract":
            observations.append(f"Extracting data from {step.target}")
        elif action == "verify":
            observations.append(f"Verifying: {step.verification}")
        else:
            observations.append(f"Executing: {action}")
        
        # Add the step description as additional context
        if step.description and step.description not in observations:
            observations.append(f"({step.description})")
        
        return " ".join(observations)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a workflow"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id].to_dict()
        return None
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = AutomationStatus.CANCELLED
            workflow.completed_at = datetime.now()
            return True
        return False


# Singleton instance
nova_act = NovaActAutomation()