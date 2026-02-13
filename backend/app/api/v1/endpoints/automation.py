"""
Automation API Endpoints
Handles Nova Act automation workflows for Calendly, CRM, and other integrations
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import json
import asyncio
from app.services.nova_act import nova_act, AutomationWorkflow, AutomationStatus
from app.services.nova_reasoning import nova_reasoning
from app.api.deps import get_current_business_id, get_current_active_user
from app.models.models import User

router = APIRouter()


class AutomationConnectionManager:
    """Manages WebSocket connections for automation progress updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        """Remove a connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_json(self, session_id: str, data: Dict[str, Any]):
        """Send JSON message to a specific connection"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)


automation_manager = AutomationConnectionManager()


@router.post("/create-calendly-workflow")
async def create_calendly_booking_workflow(
    customer_name: str,
    customer_phone: str,
    customer_email: str,
    service: str,
    date: str,
    time: str,
    calendly_url: str,
    business_id: int = Depends(get_current_business_id)
):
    """
    Create a Calendly booking workflow.
    
    This endpoint creates but doesn't execute the workflow.
    Use the WebSocket endpoint to execute with real-time progress.
    """
    try:
        workflow = nova_act.create_calendly_booking_workflow(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            service=service,
            date=date,
            time=time,
            calendly_url=calendly_url
        )
        
        return {
            "success": True,
            "workflow": workflow.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-crm-workflow")
async def create_crm_update_workflow(
    crm_type: str,
    customer_data: Dict[str, Any],
    interaction_data: Dict[str, Any],
    business_id: int = Depends(get_current_business_id)
):
    """
    Create a CRM update workflow (Salesforce or HubSpot).
    """
    try:
        workflow = nova_act.create_crm_update_workflow(
            crm_type=crm_type,
            customer_data=customer_data,
            interaction_data=interaction_data
        )
        
        return {
            "success": True,
            "workflow": workflow.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-automation-plan")
async def generate_automation_plan(
    task: str,
    reasoning_data: Dict[str, Any],
    business_id: int = Depends(get_current_business_id)
):
    """
    Use Nova Act to generate an automation plan for a given task.
    
    This analyzes the task and reasoning data to create a step-by-step
    automation workflow.
    """
    try:
        # Get business context
        from app.api.v1.endpoints.voice import _get_business_context
        business_context = await _get_business_context(business_id)
        
        # Generate automation plan
        steps = await nova_act.generate_automation_plan(
            task=task,
            reasoning_data=reasoning_data,
            business_context=business_context
        )
        
        return {
            "success": True,
            "steps": [step.to_dict() for step in steps],
            "total_steps": len(steps)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{workflow_id}")
async def automation_websocket(
    websocket: WebSocket,
    workflow_id: str,
    business_id: int = Depends(get_current_business_id)
):
    """
    WebSocket endpoint for executing automation workflows with real-time progress.
    
    Client should send a message with workflow data:
    {
        "type": "execute",
        "workflow": {workflow_object}
    }
    
    Server sends progress updates:
    {
        "type": "workflow_started" | "step_started" | "step_completed" | 
                "step_failed" | "workflow_completed" | "workflow_failed",
        "workflow_id": "...",
        "step_id": 1,
        "description": "...",
        "progress_percent": 50
    }
    """
    session_id = f"automation_{workflow_id}"
    
    try:
        await automation_manager.connect(websocket, session_id)
        
        # Receive workflow data
        data = await websocket.receive_json()
        
        if data.get("type") == "execute":
            workflow_data = data.get("workflow")
            
            if not workflow_data:
                await automation_manager.send_json(session_id, {
                    "type": "error",
                    "message": "No workflow data provided"
                })
                return
            
            # Recreate workflow object
            from app.services.nova_act import AutomationStep, AutomationAction
            
            steps = []
            for step_data in workflow_data.get("steps", []):
                step = AutomationStep(
                    step_id=step_data["step_id"],
                    action=AutomationAction(step_data["action"]),
                    description=step_data["description"],
                    target=step_data.get("target"),
                    value=step_data.get("value"),
                    selector=step_data.get("selector"),
                    wait_ms=step_data.get("wait_ms"),
                    verification=step_data.get("verification")
                )
                steps.append(step)
            
            workflow = AutomationWorkflow(
                workflow_id=workflow_data["workflow_id"],
                name=workflow_data["name"],
                description=workflow_data["description"],
                steps=steps,
                metadata=workflow_data.get("metadata", {})
            )
            
            # Execute workflow and stream progress
            async for update in nova_act.execute_workflow(workflow):
                await automation_manager.send_json(session_id, update)
        
        else:
            await automation_manager.send_json(session_id, {
                "type": "error",
                "message": f"Unknown message type: {data.get('type')}"
            })
    
    except WebSocketDisconnect:
        automation_manager.disconnect(session_id)
    except Exception as e:
        await automation_manager.send_json(session_id, {
            "type": "error",
            "message": str(e)
        })
        automation_manager.disconnect(session_id)


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    business_id: int = Depends(get_current_business_id)
):
    """
    Get the current status of an automation workflow.
    """
    status = nova_act.get_workflow_status(workflow_id)
    
    if status:
        return {
            "success": True,
            "workflow": status
        }
    else:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/cancel/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    business_id: int = Depends(get_current_business_id)
):
    """
    Cancel a running automation workflow.
    """
    success = nova_act.cancel_workflow(workflow_id)
    
    if success:
        return {
            "success": True,
            "message": f"Workflow {workflow_id} cancelled"
        }
    else:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/execute-full-booking-workflow")
async def execute_full_booking_workflow(
    customer_name: str,
    customer_phone: str,
    customer_email: str,
    service: str,
    date: str,
    time: str,
    calendly_url: str,
    crm_type: Optional[str] = None,
    business_id: int = Depends(get_current_business_id)
):
    """
    Execute a complete booking workflow: Calendly booking + optional CRM update.
    
    This is a convenience endpoint that creates and executes both workflows
    in sequence, returning the combined results.
    """
    try:
        results = []
        
        # Step 1: Calendly booking
        calendly_workflow = nova_act.create_calendly_booking_workflow(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            service=service,
            date=date,
            time=time,
            calendly_url=calendly_url
        )
        
        calendly_steps = []
        async for update in nova_act.execute_workflow(calendly_workflow):
            calendly_steps.append(update)
        
        results.append({
            "workflow": "calendly_booking",
            "updates": calendly_steps,
            "success": calendly_workflow.status == AutomationStatus.COMPLETED
        })
        
        # Step 2: CRM update (if specified)
        if crm_type:
            crm_workflow = nova_act.create_crm_update_workflow(
                crm_type=crm_type,
                customer_data={
                    "name": customer_name,
                    "phone": customer_phone,
                    "email": customer_email
                },
                interaction_data={
                    "service": service,
                    "date": date,
                    "time": time,
                    "booked_at": str(datetime.now())
                }
            )
            
            crm_steps = []
            async for update in nova_act.execute_workflow(crm_workflow):
                crm_steps.append(update)
            
            results.append({
                "workflow": f"{crm_type}_crm_update",
                "updates": crm_steps,
                "success": crm_workflow.status == AutomationStatus.COMPLETED
            })
        
        # Overall success
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "results": results,
            "total_workflows": len(results),
            "successful_workflows": sum(1 for r in results if r["success"])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))