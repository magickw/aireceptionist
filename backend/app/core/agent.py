from typing import List, Dict, Any
import json
from app.services.nova_service import nova_service

class AgentCore:
    def __init__(self):
        self.system_prompt = """
You are a helpful and efficient AI receptionist for a dental clinic called "Smile Care".
Your goals are:
1. Schedule appointments.
2. Answer questions about services (Cleaning, Whitening, Checkup).
3. Handle cancellations.

Today is Thursday, February 12, 2026.

Available tools:
- check_availability(date: str)
- book_appointment(name: str, date: str, time: str, service: str)

If you need more information to call a tool, ask the user.
If you have performed an action, confirm it to the user.
Keep responses conversational and short (under 2 sentences) suitable for voice.
"""
        self.messages = []

    def process_input(self, user_text: str):
        # 1. Add user message
        self.messages.append({"role": "user", "content": [{"text": user_text}]})
        
        # 2. Call LLM
        response_message = nova_service.generate_response(self.messages)
        
        # 3. Add assistant response to history
        self.messages.append(response_message)
        
        # 4. Extract text
        response_text = response_message['content'][0]['text']
        
        # TODO: Handle Tool Use (Function Calling) parsing here if using raw prompting, 
        # or use Bedrock's toolUse structure.
        
        return response_text

agent_core = AgentCore()
