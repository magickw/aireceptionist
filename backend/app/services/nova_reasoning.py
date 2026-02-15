"""
Nova 2 Lite Reasoning Core
Autonomous Business Operations Agent - Reasoning Engine
"""
import boto3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.core.config import settings
from app.services.knowledge_base import knowledge_base_service
from app.services.business_templates import BusinessTypeTemplate




async def get_training_context(business_id: int, db, conversation: str = "") -> str:
    """Get relevant training scenarios for the current conversation."""
    if not db or not business_id:
        return ""
    
    try:
        from app.models.models import AITrainingScenario
        
        scenarios = db.query(AITrainingScenario).filter(
            AITrainingScenario.business_id == business_id,
            AITrainingScenario.is_active == True
        ).all()
        
        if not scenarios:
            return ""
        
        conversation_lower = conversation.lower()
        relevant = []
        
        for scenario in scenarios:
            keywords = scenario.user_input.lower().split()
            match_count = sum(1 for kw in keywords if len(kw) > 3 and kw in conversation_lower)
            
            if match_count > 0 or not conversation:
                relevant.append({
                    "user_input": scenario.user_input,
                    "expected_response": scenario.expected_response,
                    "category": scenario.category,
                    "match_score": match_count
                })
        
        if not relevant:
            relevant = [
                {"user_input": s.user_input, "expected_response": s.expected_response, "category": s.category, "match_score": 0}
                for s in scenarios[:5]
            ]
        
        relevant.sort(key=lambda x: x["match_score"], reverse=True)
        
        training_text = "\n\n## Training Examples (follow these response patterns):\n"
        for i, r in enumerate(relevant[:5], 1):
            training_text += f"\nExample {i} ({r['category']}):\n"
            training_text += f"Customer: {r['user_input']}\n"
            response_preview = r['expected_response'][:150] + "..." if len(r['expected_response']) > 150 else r['expected_response']
            training_text += f"Response: {response_preview}\n"
        
        return training_text
        
    except Exception as e:
        print(f"Error fetching training context: {e}")
        return ""


class NovaReasoningEngine:
    """
    Nova 2 Lite-powered reasoning engine for autonomous business operations.
    Handles intent detection, entity extraction, action selection, and planning.
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
        
        # Available actions for the agent
        self.available_actions = [
            "CREATE_APPOINTMENT",
            "PROVIDE_INFO",
            "TRANSFER_HUMAN",
            "UPDATE_CRM",
            "HANDLE_COMPLAINT",
            "COLLECT_INFO",
            "RESCHEDULE_APPOINTMENT",
            "CANCEL_APPOINTMENT",
            "TAKE_MESSAGE"
        ]
    
    async def reason(
        self,
        conversation: str,
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        db=None
    ) -> Dict[str, Any]:
        """
        Main reasoning method - analyzes conversation and determines best action.
        
        Args:
            conversation: Current conversation transcript
            business_context: Business information (type, services, hours, etc.)
            customer_context: Customer information (history, preferences, etc.)
            db: Database session for knowledge base lookup
            
        Returns:
            Structured reasoning result with intent, entities, action, and metadata
        """
        
        # Try to get relevant context from knowledge base
        knowledge_context = ""
        if db and business_context.get("business_id"):
            try:
                knowledge_context = await knowledge_base_service.get_relevant_context(
                    query=conversation,
                    business_id=business_context.get("business_id"),
                    db=db,
                    max_chars=1500
                )
            except Exception as e:
                print(f"Knowledge base lookup failed: {e}")
        
        # Get training context
        training_context = ""
        if db and business_context.get("business_id"):
            try:
                from app.services.nova_reasoning import get_training_context
                training_context = await get_training_context(
                    business_id=business_context.get("business_id"),
                    db=db,
                    conversation=conversation
                )
            except Exception as e:
                print(f"Training context lookup failed: {e}")
        
        system_prompt = self._build_system_prompt(business_context, customer_context, knowledge_context, training_context)
        
        messages = [
            {"role": "user", "content": [{"text": conversation}]}
        ]
        
        try:
            response = await self._invoke_nova_lite(system_prompt, messages)
            
            # Parse and validate the response
            reasoning_result = self._parse_reasoning_response(response)
            
            # Add reasoning chain for visualization
            reasoning_result["reasoning_chain"] = self._build_reasoning_chain(
                reasoning_result, business_context, customer_context
            )
            
            return reasoning_result
            
        except Exception as e:
            # Fallback to safe defaults if reasoning fails
            return self._get_fallback_response(str(e))
    
    def _build_system_prompt(
        self,
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        knowledge_context: str = "",
        training_context: str = ""
    ) -> str:
        """
        Build comprehensive system prompt with all context.
        """
        
        # Build knowledge base context if available
        kb_section = ""
        if knowledge_context:
            kb_section = f"""
## Knowledge Base Context:
{knowledge_context}

**Use this knowledge base information to answer customer questions accurately.**
"""
        
        # Build menu context if available (for restaurants, retail, etc.)
        menu_section = ""
        menu = business_context.get('menu', [])
        if menu:
            menu_items_text = []
            # Group by category
            by_category = {}
            for item in menu:
                cat = item.get('category', 'Other')
                if cat not in by_category:
                    by_category[cat] = []
                price_str = f"${item['price']:.2f}" if item.get('price') else "Price TBD"
                by_category[cat].append(f"- {item['name']}: {price_str}" + (f" ({item.get('description', '')})" if item.get('description') else ""))
            
            for cat, items in by_category.items():
                menu_items_text.append(f"\n### {cat}:\n" + "\n".join(items))
            
            menu_section = f"""
- Menu/Products Available:
{''.join(menu_items_text)}

**Use this menu information to help customers with orders, answer pricing questions, and make recommendations.**
"""
        
        # Get business type template for specialized behavior
        business_type = business_context.get('type', 'general')
        template_prompt = BusinessTypeTemplate.get_template_prompt(business_type)
        
        # Get required info fields for this business type
        required_info = BusinessTypeTemplate.get_required_info(business_type)
        
        prompt = f"""
You are Nova 2 Lite, the reasoning core of an autonomous business operations agent.

Your role: Analyze customer calls, determine intent, select appropriate actions, and guide autonomous workflows.

## Available Actions:
{self._format_actions_list()}

## Business Context:
- Business Name: {business_context.get('name', 'Unknown')}
- Business Type: {business_type.title()}
- Services: {', '.join(business_context.get('services', []))}
- Operating Hours: {business_context.get('operating_hours', 'Not specified')}
- Available Slots: {', '.join(business_context.get('available_slots', []))}
{menu_section}

## Required Information to Collect:
When handling customer requests, always collect: {', '.join(required_info)}

{template_prompt}

## Customer Context:
- Name: {customer_context.get('name', 'Unknown')}
- Phone: {customer_context.get('phone', 'Unknown')}
- Previous Calls: {customer_context.get('call_count', 0)}
- Last Contact: {customer_context.get('last_contact', 'Never')}
- Satisfaction Score: {customer_context.get('satisfaction_score', 0)}/5.0
- Preferred Services: {', '.join(customer_context.get('preferred_services', []))}
- Previous Complaints: {customer_context.get('complaint_count', 0)}
{kb_section}
{training_context}

## Response Format (strict JSON):
{{
  "intent": "<PRIMARY_INTENT>",
  "confidence": <0.0-1.0>,
  "entities": {{
    "service": "<extracted_service_or_null>",
    "date": "<preferred_date_or_null>",
    "time": "<preferred_time_or_null>",
    "customer_name": "<extracted_name_or_null>",
    "customer_phone": "<extracted_phone_or_null>",
    "urgency": "<low|medium|high>",
    "issue_type": "<complaint_type_or_null>"
  }},
  "selected_action": "<ONE_OF_AVAILABLE_ACTIONS>",
  "action_reasoning": "<Why this action was selected (2-3 sentences)>",
  "next_questions": ["<question1>", "<question2>"],
  "sentiment": "<positive|neutral|negative>",
  "escalation_risk": <0.0-1.0>,
  "memory_update": {{
    "key": "<update_type>",
    "value": "<update_value>"
  }},
  "suggested_response": "<What AI should say to customer>"
}}

## Reasoning Chain:
1. Identify customer intent from conversation
2. Extract relevant entities (service, date, time, etc.)
3. Check customer history for context
4. Match intent to best action
5. Identify missing information needed
6. Assess sentiment and escalation risk
7. Plan memory updates
8. Draft appropriate response

## Special Cases:
- If customer mentions "complaint", "unhappy", "manager", "terrible" → Check escalation_risk > 0.7
- If VIP customer (satisfaction > 4.5) → Set escalation_risk < 0.3, prioritize
- If repeat issue in history → Flag for human review, escalate
- If after hours → Suggest alternative or queue appointment
- If customer angry (negative sentiment + high urgency) → Consider TRANSFER_HUMAN
- **IMPORTANT - Appointment Booking**: Before confirming ANY appointment, you MUST collect: (1) customer's full name, (2) phone number. Use COLLECT_INFO action until you have both name AND phone, then use CREATE_APPOINTMENT

## Quality Guidelines:
- Confidence should reflect how clearly the intent is expressed
- Only extract entities if explicitly mentioned
- Action reasoning should be specific and contextual
- Next questions should be minimal - only ask what's needed
- Escalation risk should account for both sentiment and history
"""
        return prompt
    
    def _format_actions_list(self) -> str:
        """Format available actions with descriptions."""
        descriptions = {
            "CREATE_APPOINTMENT": "Book new appointments via Calendly",
            "PROVIDE_INFO": "Answer business questions (hours, services, pricing)",
            "TRANSFER_HUMAN": "Escalate complex issues to human agent",
            "UPDATE_CRM": "Sync customer data to Salesforce/HubSpot",
            "HANDLE_COMPLAINT": "Address service issues and concerns",
            "COLLECT_INFO": "Gather missing customer information",
            "RESCHEDULE_APPOINTMENT": "Modify existing appointment times",
            "CANCEL_APPOINTMENT": "Cancel scheduled appointments",
            "TAKE_MESSAGE": "Record message for callback"
        }
        
        return "\n".join([
            f"{action}: {desc}" 
            for action, desc in descriptions.items()
        ])
    
    async def _invoke_nova_lite(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """
        Invoke Nova 2 Lite model with structured reasoning prompt.
        """
        body = {
            "messages": messages,
            "system": [{"text": system_prompt}],
            "inferenceConfig": {
                "maxTokens": 1024,
                "temperature": 0.1,
                "topP": 0.9
            }
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response["body"].read().decode())
        
        # Extract the content from the response
        if "messages" in response_body and len(response_body["messages"]) > 0:
            content = response_body["messages"][0].get("content", "")
            # Handle both string and list content
            if isinstance(content, list):
                # Join text from all content blocks
                return "".join([block.get("text", "") for block in content if block.get("text")])
            return content
        elif "output" in response_body:
            content = response_body["output"].get("message", {}).get("content", {})
            if isinstance(content, list):
                return "".join([block.get("text", "") for block in content if block.get("text")])
            return content
        else:
            raise ValueError(f"Unexpected response format: {response_body}")
    
    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate the reasoning response.
        """
        # Debug: print raw response
        print(f"[Nova Reasoning] Raw response: {response[:1000]}...")
        
        try:
            # Try to extract JSON from the response
            if isinstance(response, dict):
                result = response
            else:
                # First, clean up the response - remove markdown code blocks
                import re
                
                # Remove markdown code block markers (```json, ```, etc.)
                cleaned_response = re.sub(r'```json\s*', '', response, flags=re.IGNORECASE)
                cleaned_response = re.sub(r'```\s*$', '', cleaned_response, flags=re.MULTILINE)
                cleaned_response = cleaned_response.strip()
                
                print(f"[Nova Reasoning] Cleaned response: {cleaned_response[:500]}...")
                
                # Try to parse the entire cleaned response as JSON (not regex)
                try:
                    result = json.loads(cleaned_response)
                    print(f"[Nova Reasoning] Successfully parsed full JSON, intent: {result.get('intent')}")
                except json.JSONDecodeError as e:
                    print(f"[Nova Reasoning] Failed to parse full JSON: {e}")
                    # Last resort: try regex
                    json_match = re.search(r'\{[^{}]*\}', cleaned_response)
                    if json_match:
                        result = json.loads(json_match.group())
            
            # Check if result was actually defined
            if 'result' not in locals():
                raise ValueError("Could not parse JSON from response")
            
            # Validate required fields
            required_fields = [
                "intent", "confidence", "entities", "selected_action",
                "action_reasoning", "sentiment", "escalation_risk", "suggested_response"
            ]
            
            for field in required_fields:
                if field not in result:
                    print(f"[Nova Reasoning] Missing field '{field}', using default")
                    result[field] = self._get_default_value(field)
            
            # Validate selected action
            if result["selected_action"] not in self.available_actions:
                result["selected_action"] = "PROVIDE_INFO"
                result["action_reasoning"] = "Defaulted to providing information due to unclear intent"
            
            # Ensure types are correct
            result["confidence"] = float(result.get("confidence", 0.5))
            result["escalation_risk"] = float(result.get("escalation_risk", 0.1))
            
            # Ensure next_questions is a list
            if "next_questions" not in result or not isinstance(result["next_questions"], list):
                result["next_questions"] = []
            
            # Ensure memory_update exists
            if "memory_update" not in result:
                result["memory_update"] = {"key": "none", "value": None}
            
            return result
            
        except Exception as e:
            # If parsing fails, return structured error response
            return self._get_fallback_response(f"Parse error: {str(e)}")
    
    def _build_reasoning_chain(
        self,
        reasoning_result: Dict[str, Any],
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build a visible reasoning chain for the UI panel.
        """
        chain = [
            {
                "step": 1,
                "title": "Intent Detection",
                "description": f"Identified customer intent: {reasoning_result['intent']}",
                "confidence": reasoning_result['confidence']
            },
            {
                "step": 2,
                "title": "Entity Extraction",
                "description": f"Extracted entities: {json.dumps(reasoning_result['entities'])}",
                "details": reasoning_result['entities']
            },
            {
                "step": 3,
                "title": "Context Analysis",
                "description": f"Customer has {customer_context.get('call_count', 0)} previous calls, satisfaction score {customer_context.get('satisfaction_score', 0)}/5",
                "context": {
                    "call_history": customer_context.get('call_count', 0),
                    "satisfaction": customer_context.get('satisfaction_score', 0),
                    "preferred_services": customer_context.get('preferred_services', [])
                }
            },
            {
                "step": 4,
                "title": "Action Selection",
                "description": f"Selected action: {reasoning_result['selected_action']}",
                "reasoning": reasoning_result['action_reasoning']
            },
            {
                "step": 5,
                "title": "Risk Assessment",
                "description": f"Sentiment: {reasoning_result['sentiment']}, Escalation Risk: {reasoning_result['escalation_risk']*100:.1f}%",
                "risk_level": "high" if reasoning_result['escalation_risk'] > 0.7 else "medium" if reasoning_result['escalation_risk'] > 0.3 else "low"
            }
        ]
        
        # Add sentiment analysis details
        if reasoning_result['sentiment'] == 'negative':
            chain.append({
                "step": 6,
                "title": "Sentiment Alert",
                "description": "Negative sentiment detected - consider human transfer",
                "alert": True
            })
        
        # Add escalation recommendation
        if reasoning_result['escalation_risk'] > 0.7:
            chain.append({
                "step": len(chain) + 1,
                "title": "Escalation Recommendation",
                "description": "High escalation risk - recommend human intervention",
                "alert": True,
                "recommendation": "TRANSFER_HUMAN"
            })
        
        return chain
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields."""
        defaults = {
            "intent": "unknown",
            "confidence": 0.5,
            "entities": {},
            "selected_action": "PROVIDE_INFO",
            "action_reasoning": "Using default action due to unclear intent",
            "next_questions": [],
            "sentiment": "neutral",
            "escalation_risk": 0.1,
            "memory_update": {"key": "none", "value": None},
            "suggested_response": "I'd be happy to help you with that. Could you please provide more details?"
        }
        return defaults.get(field, None)
    
    def _get_fallback_response(self, error: str) -> Dict[str, Any]:
        """Get safe fallback response when reasoning fails."""
        return {
            "intent": "unknown",
            "confidence": 0.3,
            "entities": {},
            "selected_action": "PROVIDE_INFO",
            "action_reasoning": f"Unable to determine intent due to processing error: {error}",
            "next_questions": ["How can I help you today?"],
            "sentiment": "neutral",
            "escalation_risk": 0.1,
            "memory_update": {"key": "none", "value": None},
            "suggested_response": "I apologize, but I'm having trouble understanding. Could you please rephrase that?",
            "error": error,
            "reasoning_chain": [
                {
                    "step": 1,
                    "title": "Error",
                    "description": f"Reasoning failed: {error}",
                    "error": True
                }
            ]
        }


# Singleton instance
nova_reasoning = NovaReasoningEngine()
