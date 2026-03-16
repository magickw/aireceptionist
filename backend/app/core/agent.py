from typing import List, Dict, Any, Optional
import json
from app.services.nova_service import nova_service


class AgentCore:
    """
    Lightweight stateless agent for simple single-turn interactions.
    For full multi-turn voice sessions use NovaReasoningEngine + NovaSonicStreamSession.
    """

    def __init__(self, business_context: Optional[Dict[str, Any]] = None):
        ctx = business_context or {}
        business_name = ctx.get("name", "this business")
        business_type = ctx.get("type", "general")
        services = ", ".join(ctx.get("services", [])) or "general services"
        hours = ctx.get("operating_hours", "during business hours")

        self.system_prompt = f"""You are a helpful AI receptionist for {business_name} ({business_type}).
Your goals are:
1. Schedule appointments.
2. Answer questions about services: {services}.
3. Handle cancellations and general inquiries.
4. Operating hours: {hours}.

Available tools:
- check_availability(date: str, time: str)
- book_appointment(name: str, phone: str, date: str, time: str, service: str)
- cancel_appointment(appointment_id: str)

If you need more information to call a tool, ask the user.
After performing an action, confirm it concisely.
Keep responses under 2 sentences — suitable for voice."""

        self.messages: List[Dict[str, Any]] = []

    def process_input(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": [{"text": user_text}]})

        response_message = nova_service.generate_response(self.messages)
        self.messages.append(response_message)

        content = response_message.get("content", [])

        # Handle tool use blocks returned by Nova Lite
        tool_results = []
        text_parts = []

        for block in content:
            if "text" in block:
                text_parts.append(block["text"])
            elif "toolUse" in block:
                tool_result = self._execute_tool(block["toolUse"])
                tool_results.append({
                    "toolResult": {
                        "toolUseId": block["toolUse"]["toolUseId"],
                        "content": [{"text": json.dumps(tool_result)}],
                    }
                })

        # If tools were called, send results back and get final response
        if tool_results:
            self.messages.append({"role": "user", "content": tool_results})
            final_message = nova_service.generate_response(self.messages)
            self.messages.append(final_message)
            final_content = final_message.get("content", [])
            return " ".join(b["text"] for b in final_content if "text" in b).strip()

        return " ".join(text_parts).strip() or "I'm here to help. Could you please repeat that?"

    def _execute_tool(self, tool_use: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool calls to the appropriate handler."""
        name = tool_use.get("name", "")
        inputs = tool_use.get("input", {})

        if name == "check_availability":
            return {"available": True, "message": f"The slot on {inputs.get('date')} at {inputs.get('time')} is available."}
        elif name == "book_appointment":
            return {
                "success": True,
                "message": f"Appointment booked for {inputs.get('name')} on {inputs.get('date')} at {inputs.get('time')} for {inputs.get('service', 'your service')}.",
            }
        elif name == "cancel_appointment":
            return {"success": True, "message": f"Appointment {inputs.get('appointment_id')} has been cancelled."}
        else:
            return {"error": f"Unknown tool: {name}"}

    def reset(self):
        """Clear conversation history."""
        self.messages = []


# Default singleton — business context injected at runtime via constructor
agent_core = AgentCore()
