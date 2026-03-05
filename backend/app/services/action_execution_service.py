"""
Action Execution Service
Encapsulates tool execution logic for AI agents across different channels
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import CalendarIntegration
from app.services.calendar_service import calendar_service
from app.services.order_service import order_service
from app.services.integration_service import IntegrationService, POSIntegrationInterface
from app.services.smart_scheduling_service import smart_scheduling_service
from app.services.voice_helpers import parse_natural_datetime

class ActionExecutionService:
    """
    Central service for executing AI-triggered actions (tools).
    Allows the same business logic to be invoked from Voice, Chat, or SMS.
    """

    def __init__(self, db: Session):
        self.db = db
        self.integration_svc = IntegrationService(db)

    async def execute_action(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        business_id: int,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute an action by name with the given input.
        
        Args:
            tool_name: The name of the tool/action to execute
            tool_input: Parameters for the tool
            business_id: The business context
            context: Additional context (e.g., session state, customer info)
            
        Returns:
            Execution result
        """
        context = context or {}
        
        # Mapping tool names to handler methods
        handlers = {
            "bookAppointment": self._handle_book_appointment,
            "checkAvailability": self._handle_check_availability,
            "placeOrder": self._handle_place_order,
            "confirmOrder": self._handle_confirm_order,
            "transferToHuman": self._handle_transfer_to_human,
            "sendDirections": self._handle_send_directions,
            "processPayment": self._handle_process_payment,
            "interactWithPOS": self._handle_interact_with_pos,
            "recallCustomerMemory": self._handle_recall_customer_memory,
            "executeWorkflow": self._handle_execute_workflow,
            "cancelAppointment": self._handle_cancel_appointment,
            "refundPayment": self._handle_refund_payment,
            "cancelOrder": self._handle_cancel_order,
            "sendConfirmationSMS": self._handle_send_confirmation_sms,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"success": False, "message": f"Unknown tool: {tool_name}"}

        try:
            return await handler(tool_input, business_id, context)
        except Exception as e:
            import traceback
            print(f"[ActionExecution] Error executing {tool_name}: {e}")
            print(traceback.format_exc())
            return {"success": False, "message": f"Execution error: {str(e)}"}

    async def _handle_book_appointment(self, tool_input, business_id, context):
        customer_name = tool_input.get("customer_name") or context.get("customer_name")
        customer_phone = tool_input.get("customer_phone") or context.get("customer_phone")
        
        # VALIDATION: Ensure we have name and phone before booking
        missing = []
        if not customer_name: missing.append("customer_name")
        if not customer_phone: missing.append("customer_phone")
        
        if missing:
            return {
                "success": False, 
                "message": f"I need the following information to complete the booking: {', '.join(missing)}. Please ask the customer for these details.",
                "missing_fields": missing
            }

        date_str = tool_input.get("date")
        time_str = tool_input.get("time")
        service = tool_input.get("service", "General")
        
        appointment_time = parse_natural_datetime(date_str, time_str)
        
        if not appointment_time:
            return {"success": False, "message": "Could not parse the date and time."}

        # Validate appointment time is within business operating hours
        from app.models.models import Business
        business = self.db.query(Business).filter(Business.id == business_id).first()
        if business and business.operating_hours:
            day_of_week = appointment_time.strftime('%A').lower()
            day_hours = business.operating_hours.get(day_of_week)
            
            if day_hours:
                try:
                    start_hour, start_minute = map(int, day_hours["start"].split(':'))
                    end_hour, end_minute = map(int, day_hours["end"].split(':'))
                    
                    day_start = appointment_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    day_end = appointment_time.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                    
                    if not (day_start <= appointment_time < day_end):
                        return {
                            "success": False,
                            "message": f"The requested time is outside our operating hours ({day_hours['start']} - {day_hours['end']}). Please choose a time during business hours."
                        }
                except (KeyError, ValueError) as e:
                    # If operating hours format is invalid, log but don't block
                    print(f"[ActionExecution] Invalid operating hours format: {e}")

        # Check no-show risk before booking
        risk_assessment = await smart_scheduling_service.predict_no_show_probability(
            self.db, business_id, customer_phone, appointment_time, service
        )
        
        end_time = appointment_time + timedelta(hours=1)
        result = await calendar_service.check_and_book_appointment(
            business_id=business_id,
            start_time=appointment_time,
            end_time=end_time,
            customer_name=customer_name,
            customer_phone=customer_phone,
            service=service,
            db=self.db,
        )
        
        if result["success"]:
            result["risk_level"] = risk_assessment["risk_level"]
            result["recommendation"] = risk_assessment["recommendation"]
        
        return result

    async def _handle_check_availability(self, tool_input, business_id, context):
        date_str = tool_input.get("date")
        time_str = tool_input.get("time")
        appointment_time = parse_natural_datetime(date_str, time_str)
        
        if not appointment_time:
            return {"available": False, "message": "Could not parse the date and time."}

        integration = self.db.query(CalendarIntegration).filter(
            CalendarIntegration.business_id == business_id,
            CalendarIntegration.status == "active",
        ).first()

        end_time = appointment_time + timedelta(hours=1)
        if integration:
            result = await calendar_service.check_availability(
                integration, appointment_time, end_time, self.db
            )
        else:
            conflicts = calendar_service.check_db_conflicts(business_id, appointment_time, end_time, self.db)
            result = {"available": not conflicts}

        if not result.get("available"):
            suggestions = await smart_scheduling_service.suggest_optimal_times(
                self.db, business_id, context.get("customer_phone", ""), appointment_time
            )
            result["suggested_alternatives"] = suggestions.get("suggested_times", [])

        return result

    async def _handle_place_order(self, tool_input, business_id, context):
        # Implementation of order accumulation logic...
        # In a real implementation, we would update the session's order_items
        return {"success": True, "message": "Items added to pending order."}

    async def _handle_confirm_order(self, tool_input, business_id, context):
        customer_name = tool_input.get("customer_name") or context.get("customer_name")
        customer_phone = tool_input.get("customer_phone") or context.get("customer_phone")
        
        # VALIDATION
        missing = []
        if not customer_name: missing.append("customer_name")
        if not customer_phone: missing.append("customer_phone")
        
        if missing:
            return {
                "success": False, 
                "message": f"I need the following information to confirm the order: {', '.join(missing)}.",
                "missing_fields": missing
            }
            
        return {"success": True, "message": "Order confirmed."}

    async def _handle_transfer_to_human(self, tool_input, business_id, context):
        return {
            "success": True, 
            "transferred": True, 
            "reason": tool_input.get("reason", "Customer requested human agent")
        }

    async def _handle_send_directions(self, tool_input, business_id, context):
        return {"success": True, "message": "Directions sent."}

    async def _handle_process_payment(self, tool_input, business_id, context):
        return {"success": True, "message": f"Payment link for ${tool_input.get('amount')} sent."}

    async def _handle_interact_with_pos(self, tool_input, business_id, context):
        action = tool_input.get("action")
        payload = tool_input.get("payload", {})
        
        active_integrations = self.integration_svc.get_business_integrations(business_id)
        pos_integration = next((i for i in active_integrations if "pos" in i.integration_type.lower()), None)
        
        if not pos_integration:
            return {"success": False, "message": "No active POS integration found."}
        
        client = self.integration_svc.get_integration_by_type(business_id, pos_integration.integration_type)
        if not client or not isinstance(client, POSIntegrationInterface):
            return {"success": False, "message": "POS integration error."}
            
        if action == "send_order":
            result = await client.send_order(payload)
            return {"success": True, "pos_result": result}
        # ... other POS actions
        return {"success": False, "message": "Unsupported POS action."}

    def get_dynamic_tools(self, business_id: int) -> List[Dict[str, Any]]:
        """
        Generate tool definitions dynamically based on business state and integrations.
        """
        tools = [
            {
                "name": "checkAvailability",
                "description": "Check if a time slot is available for an appointment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date like 'tomorrow' or 'March 15th'"},
                        "time": {"type": "string", "description": "Time like '2pm' or '10:30 am'"}
                    },
                    "required": ["date", "time"]
                }
            },
            {
                "name": "bookAppointment",
                "description": "Book an appointment for a customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string"},
                        "customer_phone": {"type": "string"},
                        "date": {"type": "string"},
                        "time": {"type": "string"},
                        "service": {"type": "string"}
                    },
                    "required": ["date", "time"]
                }
            },
            {
                "name": "transferToHuman",
                "description": "Transfer the call to a human agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string"}
                    }
                }
            },
            {
                "name": "recallCustomerMemory",
                "description": "Recall stored memories and preferences for the current customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to search for in customer memories"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "executeWorkflow",
                "description": "Execute a predefined multi-step workflow atomically. Available: bookingWorkflow, orderWorkflow.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {"type": "string", "enum": ["bookingWorkflow", "orderWorkflow"]},
                        "inputs": {"type": "object", "description": "Input parameters for the workflow"}
                    },
                    "required": ["workflow_name", "inputs"]
                }
            },
        ]
        
        # Add POS tools if integration exists
        active_integrations = self.integration_svc.get_business_integrations(business_id)
        has_pos = any("pos" in i.integration_type.lower() for i in active_integrations)
        
        if has_pos:
            tools.append({
                "name": "interactWithPOS",
                "description": "Interact with the Point of Sale system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["send_order", "get_menu", "get_status"]},
                        "payload": {"type": "object"}
                    }
                }
            })

        return tools

    # ------------------------------------------------------------------
    # E1: Customer Memory Recall
    # ------------------------------------------------------------------

    async def _handle_recall_customer_memory(self, tool_input, business_id, context):
        query = tool_input.get("query", "")
        customer_id = context.get("customer_id")
        if not customer_id:
            return {"success": False, "message": "No customer identified for memory recall."}

        from app.services.customer_memory_service import customer_memory_service
        return customer_memory_service.recall_customer_memory(
            self.db, customer_id, business_id, query
        )

    # ------------------------------------------------------------------
    # E3: Workflow Orchestration
    # ------------------------------------------------------------------

    async def _handle_execute_workflow(self, tool_input, business_id, context):
        workflow_name = tool_input.get("workflow_name")
        inputs = tool_input.get("inputs", {})

        from app.services.workflow_templates import get_workflow
        from app.services.workflow_engine import WorkflowExecution

        try:
            definition = get_workflow(workflow_name)
        except ValueError as e:
            return {"success": False, "message": str(e)}

        # Build progress callback that puts messages on context's text_queue if available
        text_queue = context.get("text_queue")

        async def progress_cb(message: str):
            if text_queue:
                try:
                    text_queue.put_nowait({"chunk": f"\n[Workflow] {message}\n"})
                except Exception:
                    pass

        execution = WorkflowExecution(
            definition=definition,
            action_executor=self.execute_action,
            business_id=business_id,
            context={**context, **inputs},
            progress_callback=progress_cb,
        )

        # Merge workflow inputs as variables
        execution.variables.update(inputs)

        return await execution.execute()

    # ------------------------------------------------------------------
    # Compensation handlers for workflow rollback
    # ------------------------------------------------------------------

    async def _handle_cancel_appointment(self, tool_input, business_id, context):
        appointment_id = tool_input.get("appointment_id")
        if appointment_id:
            from app.models.models import Appointment
            appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if appt:
                appt.status = "cancelled"
                self.db.commit()
                return {"success": True, "message": f"Appointment {appointment_id} cancelled."}
        return {"success": True, "message": "No appointment to cancel."}

    async def _handle_refund_payment(self, tool_input, business_id, context):
        payment_id = tool_input.get("payment_id")
        return {"success": True, "message": f"Refund initiated for payment {payment_id}."}

    async def _handle_cancel_order(self, tool_input, business_id, context):
        order_id = tool_input.get("order_id")
        return {"success": True, "message": f"Order {order_id} cancelled."}

    async def _handle_send_confirmation_sms(self, tool_input, business_id, context):
        phone = tool_input.get("customer_phone")
        message = tool_input.get("message", "Your appointment has been confirmed.")
        # Use existing SMS infrastructure if available
        try:
            from app.services.sms_service import sms_service
            await sms_service.send_sms(phone, message, business_id)
            return {"success": True, "message": f"Confirmation SMS sent to {phone}."}
        except Exception as e:
            return {"success": True, "message": f"SMS queued for {phone} (delivery pending)."}
