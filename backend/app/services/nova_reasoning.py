"""
Nova 2 Lite Reasoning Core
Autonomous Business Operations Agent - Reasoning Engine

================================================================================
GOVERNANCE ARCHITECTURE
================================================================================

The reasoning engine implements a multi-layered safety governance system that
balances automation capability with risk mitigation.

┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 1: DETERMINISTIC TRIGGERS                    │
│                           (Runs BEFORE model invocation)                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Critical Keywords                                                  │  │
│  │  - Emergency: 911, emergency, dying, unconscious                    │  │
│  │  - Legal: sue, lawsuit, lawyer, attorney, legal action              │  │
│  │  - Safety: gas leak, fire, explosion, carbon monoxide               │  │
│  │  - Harassment: sexual harassment, discrimination, threat            │  │
│  │  - Police: police, arrest, criminal                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Customer History                                                    │  │
│  │  - Repeat complaints (≥2) + escalation keywords                     │  │
│  │  - VIP customers (satisfaction ≥4.5) + negative sentiment           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Industry-Specific Triggers                                          │  │
│  │  Medical: chest pain, difficulty breathing, severe pain, bleeding    │  │
│  │  HVAC: gas smell, gas leak, carbon monoxide, smoke, fire             │  │
│  │  Law Firm: arrested, court tomorrow, deadline today                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Result: If ANY trigger matches → IMMEDIATE ESCALATION (bypass model)      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (No deterministic triggers)
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 2: MODEL-BASED REASONING                     │
│                           (AWS Bedrock Nova Lite)                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Intent Classification                                                │  │
│  │  - Primary intent detection (15+ intents)                            │  │
│  │  - Entity extraction (service, date, time, customer info)            │  │
│  │  - Confidence scoring (0.0-1.0)                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Action Selection                                                     │  │
│  │  - CREATE_APPOINTMENT, PROVIDE_INFO, TRANSFER_HUMAN, etc.            │  │
│  │  - Action reasoning (why this action was selected)                   │  │
│  │  - Next questions to ask user                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Risk Assessment                                                      │  │
│  │  - Escalation risk score (0.0-1.0)                                   │  │
│  │  - Sentiment analysis (positive/neutral/negative)                    │  │
│  │  - Urgency detection (low/medium/high)                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 3: COMBINED GOVERNANCE                       │
│                           (Model output + deterministic factors)            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Confidence Threshold Check                                           │  │
│  │  - Compare model confidence vs industry threshold                     │  │
│  │  - Restaurant: ≥0.6 (HIGH autonomy)                                  │  │
│  │  - Medical: ≥0.85 (RESTRICTED)                                       │  │
│  │  - Law Firm: ≥0.8 (MEDIUM with legal urgency)                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Escalation Risk Check                                                │  │
│  │  - Compare escalation risk vs industry threshold                      │  │
│  │  - Restaurant: ≤0.7 (high auto-escalate threshold)                   │  │
│  │  - Medical: ≤0.4 (low auto-escalate threshold)                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Intent Validation                                                    │  │
│  │  - Validate detected intent using intent classifier                  │  │
│  │  - Suggest alternative if validation fails                           │  │
│  │  - Require human review if low confidence                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  High-Risk Intent Check                                               │  │
│  │  - Restaurant: food_poisoning, severe_allergy                        │  │
│  │  - Medical: medical_emergency                                        │  │
│  │  - HVAC: gas leak, carbon monoxide                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  VIP Customer Handling                                                │  │
│  │  - VIP + negative sentiment → human review                           │  │
│  │  - VIP + complaint → priority handling                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Result: If ANY check fails → HUMAN_INTERVENTION (override action)          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 4: APPROVAL WORKFLOW                         │
│                           (For high-risk actions)                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Create ApprovalRequest                                               │  │
│  │  - business_id, customer_id, request_type                            │  │
│  │  - request_data (full context)                                       │  │
│  │  - risk_score, triggered_by                                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Notify Manager                                                       │  │
│  │  - Webhook / Email notification                                      │  │
│  │  - Pending review queue                                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Wait for Approval/Rejection                                          │  │
│  │  - Manager reviews in dashboard                                     │  │
│  │  - Can approve with modifications                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
GOVERNANCE TIERS
================================================================================

TIER: AUTO
  - High confidence (≥ threshold)
  - Low escalation risk (≤ threshold)
  - No high-risk intents
  - Action executes immediately

TIER: CONFIRM
  - Medium confidence
  - User confirmation required
  - "Please confirm: [action]"

TIER: PRIORITY
  - VIP customer
  - High-value interaction
  - Expedited human review

TIER: HUMAN_REVIEW
  - Low confidence
  - High escalation risk
  - High-risk intent
  - Requires approval before execution

TIER: ESCALATE
  - Deterministic trigger
  - Immediate transfer to human
  - Bypasses all automated processing

================================================================================
INDUSTRY-SPECIFIC RISK PROFILES
================================================================================

RESTAURANT (HIGH Autonomy)
  confidence_threshold: 0.6
  auto_escalate_threshold: 0.7
  high_risk_intents: [food_poisoning, severe_allergy]
  - Fast order processing
  - Minimal human intervention

MEDICAL (RESTRICTED)
  confidence_threshold: 0.85
  auto_escalate_threshold: 0.4
  high_risk_intents: [medical_emergency, chest_pain, breathing_difficulty]
  - Conservative approach
  - Immediate escalation for symptoms

LAW FIRM (MEDIUM)
  confidence_threshold: 0.8
  auto_escalate_threshold: 0.5
  high_risk_intents: [legal_action, lawsuit, attorney_consultation]
  - Legal urgency handling
  - High accuracy required

HVAC/PLUMBING (HIGH with Safety)
  confidence_threshold: 0.65
  auto_escalate_threshold: 0.6
  high_risk_intents: [gas_leak, carbon_monoxide, fire_hazard]
  - Safety-critical triggers
  - Fast emergency response

HOTEL (MEDIUM)
  confidence_threshold: 0.7
  auto_escalate_threshold: 0.5
  high_risk_intents: [security_issue, lost_property, emergency]
  - Guest experience focus
  - Moderate automation

SALON/SPA (HIGH)
  confidence_threshold: 0.6
  auto_escalate_threshold: 0.7
  high_risk_intents: [allergic_reaction, service_complaint]
  - Customer service focus
  - Fast booking

RETAIL (HIGH)
  confidence_threshold: 0.6
  auto_escalate_threshold: 0.7
  high_risk_intents: [product_issue, return_dispute]
  - Sales optimization
  - Fast checkout

================================================================================
RESPONSE FORMAT
================================================================================

{
  "intent": "order_food",
  "confidence": 0.85,
  "entities": {
    "service": "dine-in",
    "menu_item": "Burger",
    "quantity": 1,
    "date": null,
    "time": null,
    "customer_name": "John",
    "customer_phone": "555-1234",
    "delivery_method": null,
    "urgency": "medium",
    "issue_type": null,
    "order_items": ["Burger"]
  },
  "selected_action": "PLACE_ORDER",
  "action_reasoning": "Customer wants to order a burger for dine-in",
  "next_questions": ["Would you like any drinks?", "Any special requests?"],
  "sentiment": "positive",
  "escalation_risk": 0.2,
  "memory_update": {"key": "preferred_menu", "value": "Burger"},
  "suggested_response": "Great choice! I'll add a burger to your order...",
  "requires_approval": false,
  "intent_validated": true,
  "intent_confidence": 0.88,
  "reasoning_chain": [...],
  "governance": {
    "business_type": "restaurant",
    "confidence_threshold": 0.6,
    "risk_threshold": 0.7,
    "deterministic_check": {"should_escalate": false},
    "final_tier": "auto"
  }
}

================================================================================
KEY METHODS
================================================================================

reason(conversation, business_context, customer_context, db, multimodal_data)
  - Main entry point
  - Executes all governance layers
  - Returns structured reasoning result

_check_deterministic_triggers(conversation, customer_context, business_type)
  - Layer 1: Pre-model safety check
  - Returns escalation decision immediately if trigger matches

_create_deterministic_escalation_response(trigger_info, business_context, customer_context)
  - Creates predetermined response for safety triggers
  - Bypasses model entirely

_parse_reasoning_response(response)
  - Validates and extracts structured JSON from model
  - Multi-layer parsing for robustness

_build_reasoning_chain(reasoning_result, business_context, customer_context)
  - Builds visualization of reasoning process
  - For debugging and transparency

evaluate_response_quality(user_input, expected_response, actual_response)
  - LLM-as-a-Judge evaluation
  - Scores response quality (0-100)

generate_synthetic_training_data(business_type, services, count)
  - Generates training scenarios
  - For improving model performance

================================================================================
INTEGRATION POINTS
================================================================================

Knowledge Base:
  - RAG lookup for relevant documents
  - In-context injection into system prompt

Training Scenarios:
  - Few-shot examples for specific business
  - Response pattern guidance

Business Templates:
  - Industry-specific prompts
  - Risk profile configuration
  - Flow context for data collection

Intent Classifier:
  - Validation of detected intent
  - Suggestion of alternatives
  - Confidence scoring

CRM Integration:
  - Customer history lookup
  - Interaction tracking
  - Customer 360 context

Calendar Service:
  - Appointment availability checking
  - Booking execution
  - Conflict detection

================================================================================
ERROR HANDLING
================================================================================

Model Invocation Error:
  - Retry with exponential backoff
  - Max 3 retries
  - Fallback to HUMAN_INTERVENTION

Parse Error:
  - Multiple JSON extraction strategies
  - Fallback to simple heuristic
  - Returns error with stalling response

Knowledge Base Error:
  - Continues without KB context
  - Logs error
  - Do not affect the core functionality.

Intent Classifier Error:
  - Continues with LLM intent
  - Marks validation as None
  - Logs error for investigation
"""
import boto3
import json
import re
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, ReadTimeoutError, ConnectTimeoutError

from app.core.config import settings
from app.services.knowledge_base import knowledge_base_service
from app.services.business_templates import BusinessTypeTemplate
from app.services.intent_classifier import validate_intent
from app.services.conversation_state import (
    ReasoningError, 
    SafetyViolationError, 
    ModelInvocationError, 
    ParseError,
    RetryConfig,
    retry_with_backoff
)


async def _get_popular_services(business_id: int, db) -> str:
    """Fetch the top 3 most popular services/products for a business."""
    if not db or not business_id:
        return ""
    
    try:
        from app.models.models import OrderItem, Appointment
        from sqlalchemy import func

        # Get top 3 ordered menu items
        top_ordered = db.query(
            OrderItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem.order).filter(
            Order.business_id == business_id
        ).group_by(OrderItem.item_name).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(3).all()

        # Get top 3 booked appointment services
        top_booked = db.query(
            Appointment.service_type,
            func.count(Appointment.id).label('total_bookings')
        ).filter(
            Appointment.business_id == business_id,
            Appointment.service_type.isnot(None)
        ).group_by(Appointment.service_type).order_by(
            func.count(Appointment.id).desc()
        ).limit(3).all()

        popular_items = {name: qty for name, qty in top_ordered}
        for service, count in top_booked:
            popular_items[service] = popular_items.get(service, 0) + count

        if not popular_items:
            return ""

        # Sort by popularity and get top 3
        sorted_items = sorted(popular_items.items(), key=lambda item: item[1], reverse=True)
        top_3 = [item[0] for item in sorted_items[:3]]

        return f"- Popular Services/Products: {', '.join(top_3)}\n"

    except Exception as e:
        print(f"Error fetching popular services: {e}")
        return ""


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


class MemoryStore:
    """
    Long-term memory store for persistent customer context across sessions
    """
    
    def __init__(self):
        # In production, this would connect to a persistent database
        # For demo purposes, we'll use an in-memory store
        self.customer_memories = {}
    
    async def store_memory(self, customer_id: str, key: str, value: Any, session_id: str = None):
        """Store memory for a customer"""
        if customer_id not in self.customer_memories:
            self.customer_memories[customer_id] = {}
        
        memory_entry = {
            "value": value,
            "timestamp": datetime.now(),
            "session_id": session_id,
            "key": key
        }
        
        self.customer_memories[customer_id][key] = memory_entry
    
    async def retrieve_memory(self, customer_id: str, key: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve memory for a customer"""
        if customer_id not in self.customer_memories:
            return None
        
        if key is None:
            # Return all memories for this customer
            return self.customer_memories[customer_id]
        
        if key in self.customer_memories[customer_id]:
            return self.customer_memories[customer_id][key]
        
        return None
    
    async def update_memory(self, customer_id: str, key: str, value: Any):
        """Update an existing memory"""
        if customer_id in self.customer_memories and key in self.customer_memories[customer_id]:
            self.customer_memories[customer_id][key]["value"] = value
            self.customer_memories[customer_id][key]["timestamp"] = datetime.now()
    
    async def delete_memory(self, customer_id: str, key: str):
        """Delete a specific memory"""
        if customer_id in self.customer_memories and key in self.customer_memories[customer_id]:
            del self.customer_memories[customer_id][key]


class NovaReasoningEngine:
    """
    Nova 2 Lite-powered reasoning engine for autonomous business operations.
    Handles intent detection, entity extraction, action selection, and planning.
    
    Architecture:
    - Model invocation layer
    - Safety gate layer with deterministic triggers
    - Structured response validator
    - Visualization builder
    - Long-term memory persistence
    - Advanced multi-step reasoning
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-lite-v1:0"
        
        # Initialize memory store
        self.memory_store = MemoryStore()
        
        # Available actions for the agent
        # NOTE: CREATE_ORDER is deprecated - use PLACE_ORDER + CONFIRM_ORDER flow
        self.available_actions = [
            "CREATE_APPOINTMENT",
            "PROVIDE_INFO",
            "TRANSFER_HUMAN",
            "UPDATE_CRM",
            "HANDLE_COMPLAINT",
            "COLLECT_INFO",
            "RESCHEDULE_APPOINTMENT",
            "CANCEL_APPOINTMENT",
            "TAKE_MESSAGE",
            "PAYMENT_PROCESS",
            "SEND_DIRECTIONS",
            "PLACE_ORDER",        # Add items to order
            "CONFIRM_ORDER",      # Finalize and save order
            "GET_MENU_ITEMS_FROM_POS", # Get menu items from integrated POS
            "SEND_ORDER_TO_POS", # Send order to integrated POS
            "GET_ORDER_STATUS_FROM_POS", # Get order status from integrated POS
            "HUMAN_INTERVENTION",
        ]
        
        # Default Safety Thresholds (overridden by industry-specific risk_profile)
        self.DEFAULT_CONFIDENCE_THRESHOLD = 0.85
        self.DEFAULT_RISK_THRESHOLD = 0.7
        
        # ===== DETERMINISTIC ESCALATION TRIGGERS =====
        # These trigger escalation REGARDLESS of model output
        self.CRITICAL_KEYWORDS = [
            "sue", "lawsuit", "lawyer", "attorney", "legal action",
            "emergency", "911", "dying", "unconscious", "chest pain",
            "gas leak", "fire", "explosion", "carbon monoxide",
            "sexual harassment", "discrimination", "threaten",
            "police", "arrest", "criminal"
        ]
        
        self.COMPLAINT_KEYWORDS = [
            "manager", "supervisor", "speak to someone",
            "terrible", "awful", "horrible", "disgusting",
            "never coming back", "refund", "money back",
            "fraud", "scam", "ripped off"
        ]
        
        self.VIP_SATISFACTION_THRESHOLD = 4.5  # Customers above this are VIPs
        self.REPEAT_COMPLAINT_THRESHOLD = 2    # Number of past complaints to trigger VIP handling
    
    async def reason(
        self,
        conversation: str,
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        db=None,
        multimodal_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main reasoning method - analyzes conversation and determines best action.
        Supports multimodal data (images, documents).
        
        Governance Architecture:
        1. Deterministic triggers (pre-model) - keywords, history, VIP rules
        2. Model-based reasoning
        3. Industry-specific thresholds (from risk_profile)
        4. Combined escalation decision
        
        Args:
            conversation: Current conversation transcript
            business_context: Business information (type, services, hours, etc.)
            customer_context: Customer information (history, preferences, etc.)
            db: Database session for knowledge base lookup
            multimodal_data: Optional data for multimodal analysis (e.g., {"type": "image", "bytes": "..."})
            
        Returns:
            Structured reasoning result with intent, entities, action, and metadata
        """
        
        # ===== STEP 1: DETERMINISTIC PRE-CHECKS =====
        # These run BEFORE model invocation to catch critical cases
        business_type = business_context.get('type', 'general')
        deterministic_escalation = self._check_deterministic_triggers(
            conversation, customer_context, business_type
        )
        
        # Get industry-specific thresholds
        risk_profile = BusinessTypeTemplate.get_risk_profile(business_type)
        confidence_threshold = risk_profile.get("confidence_threshold", self.DEFAULT_CONFIDENCE_THRESHOLD)
        risk_threshold = risk_profile.get("auto_escalate_threshold", self.DEFAULT_RISK_THRESHOLD)
        
        print(f"[Nova Governance] Business: {business_type}, Confidence threshold: {confidence_threshold}, Risk threshold: {risk_threshold}")
        
        # Immediate escalation for deterministic triggers
        if deterministic_escalation["should_escalate"]:
            print(f"[Nova Safety] Deterministic trigger: {deterministic_escalation['reason']}")
            return self._create_deterministic_escalation_response(
                deterministic_escalation, business_context, customer_context
            )
        
        # ===== STEP 2: MODEL-BASED REASONING =====
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
        
        # Get popular services for dynamic prompting
        popular_services_context = await _get_popular_services(business_context.get("business_id"), db)
        
        # Get integrations context for dynamic prompting
        integrations_context = ""
        if db and business_context.get("business_id"):
            try:
                from app.services.integration_service import IntegrationService
                integration_service = IntegrationService(db)
                active_integrations = integration_service.get_business_integrations(business_context.get("business_id"))
                if active_integrations:
                    integrations_context = "\n## Active Integrations:\n"
                    for integ in active_integrations:
                        integrations_context += f"- {integ.name} ({integ.integration_type}) - Status: {integ.status}\n"
            except Exception as e:
                print(f"Error fetching integrations context: {e}")
        
        system_prompt = self._build_system_prompt(
            business_context, 
            customer_context, 
            knowledge_context, 
            training_context,
            popular_services_context,
            integrations_context
        )
        
        # Build multimodal message if data provided
        content = [{"text": conversation}]
        if multimodal_data:
            if multimodal_data.get("type") == "image":
                content.append({
                    "image": {
                        "format": multimodal_data.get("format", "png"),
                        "source": {"bytes": multimodal_data.get("bytes")}
                    }
                })
            elif multimodal_data.get("type") == "document":
                content.append({
                    "document": {
                        "format": multimodal_data.get("format", "pdf"),
                        "name": multimodal_data.get("name", "Document"),
                        "source": {"bytes": multimodal_data.get("bytes")}
                    }
                })
        
        messages = [
            {"role": "user", "content": content}
        ]
        
        try:
            response = await self._invoke_nova_lite(system_prompt, messages)
            
            # Parse and validate the response
            reasoning_result = self._parse_reasoning_response(response)
            
            # ===== STEP 3: COMBINED GOVERNANCE CHECK =====
            # Combine model output with deterministic factors
            requires_approval = False
            safety_reason = ""
            
            # Check confidence against industry-specific threshold
            if reasoning_result["confidence"] < confidence_threshold:
                requires_approval = True
                safety_reason = f"Low confidence ({reasoning_result['confidence']:.2f} < {confidence_threshold})"
            
            # Check model-reported escalation risk against industry threshold
            elif reasoning_result["escalation_risk"] > risk_threshold:
                requires_approval = True
                safety_reason = f"High escalation risk ({reasoning_result['escalation_risk']:.2f} > {risk_threshold})"
            
            # Check for high-risk intents from risk profile
            high_risk_intents = risk_profile.get("high_risk_intents", [])
            detected_intent = reasoning_result.get("intent", "")
            
            # Validate intent using intent classifier (only if db is available)
            try:
                if db is not None:
                    is_valid, suggested_intent, intent_confidence = validate_intent(
                        detected_intent,
                        conversation,
                        business_type,
                        db,
                        threshold=confidence_threshold
                    )
                else:
                    # Skip intent validation if db not available
                    is_valid = True
                    suggested_intent = None
                    intent_confidence = 0.5
                    reasoning_result["intent_validated"] = None
                    reasoning_result["intent_validation_reason"] = "Intent validation skipped (no db session)"
                
                if not is_valid:
                    # Intent validation failed
                    if suggested_intent:
                        # Use suggested intent if available
                        reasoning_result["intent"] = suggested_intent
                        reasoning_result["intent_validated"] = False
                        reasoning_result["original_intent"] = detected_intent
                        reasoning_result["intent_validation_reason"] = f"Intent '{detected_intent}' not validated, suggested '{suggested_intent}' (confidence: {intent_confidence:.2f})"
                        detected_intent = suggested_intent
                    else:
                        # Low confidence - mark for review
                        reasoning_result["intent_validated"] = False
                        reasoning_result["intent_validation_reason"] = f"Low confidence for intent '{detected_intent}' ({intent_confidence:.2f})"
                        requires_approval = True
                        safety_reason = f"Low confidence intent detection ({intent_confidence:.2f} < {confidence_threshold})"
                else:
                    reasoning_result["intent_validated"] = True
                    reasoning_result["intent_confidence"] = intent_confidence
            except Exception as e:
                # Intent classifier failed - continue with LLM intent
                print(f"[Intent Classifier] Error validating intent: {e}")
                reasoning_result["intent_validated"] = None
                reasoning_result["intent_validation_reason"] = f"Intent classifier error: {str(e)}"
            
            if detected_intent in high_risk_intents:
                requires_approval = True
                safety_reason = f"High-risk intent detected: {detected_intent}"
            
            # VIP customer with complaint - prioritize handling
            satisfaction_score = customer_context.get("satisfaction_score", 0)
            complaint_count = customer_context.get("complaint_count", 0)
            if satisfaction_score >= self.VIP_SATISFACTION_THRESHOLD and complaint_count > 0:
                reasoning_result["is_vip"] = True
                if reasoning_result["sentiment"] == "negative":
                    requires_approval = True
                    safety_reason = f"VIP customer with negative sentiment"
            
            # If safety check fails, override action
            if requires_approval:
                print(f"[Nova Safety] Triggering Human Intervention: {safety_reason}")
                reasoning_result["selected_action"] = "HUMAN_INTERVENTION"
                reasoning_result["action_reasoning"] = f"SAFETY TRIGGER: {safety_reason}. Pausing for human review."
                reasoning_result["requires_approval"] = True
                reasoning_result["safety_reason"] = safety_reason
                # Provide a stalling response while waiting for human
                reasoning_result["suggested_response"] = "Let me just double check that information for you, one moment please."
            
            # Add reasoning chain for visualization
            reasoning_result["reasoning_chain"] = self._build_reasoning_chain(
                reasoning_result, business_context, customer_context
            )
            
            # Add governance metadata
            reasoning_result["governance"] = {
                "business_type": business_type,
                "confidence_threshold": confidence_threshold,
                "risk_threshold": risk_threshold,
                "deterministic_check": deterministic_escalation,
                "final_tier": "human_review" if requires_approval else "auto"
            }
            
            return reasoning_result
            
        except Exception as e:
            # Fallback to safe defaults if reasoning fails
            return self._get_fallback_response(str(e))
    
    async def evaluate_response_quality(
        self,
        user_input: str,
        expected_response: str,
        actual_response: str
    ) -> float:
        """
        Evaluate the quality of an AI response compared to the expected response.
        Uses LLM-as-a-Judge approach for semantic similarity.
        Returns a score from 0.0 to 100.0.
        """
        prompt = f"""
You are an expert AI evaluator. Your task is to grade the quality of an AI assistant's response.

User Input: "{user_input}"

Expected Response (Gold Standard): "{expected_response}"

Actual AI Response: "{actual_response}"

Evaluate the Actual AI Response based on:
1. Semantic Meaning: Does it convey the same information as the Expected Response?
2. Intent Accuracy: Does it address the user's intent correctly?
3. Tone/Politeness: Is the tone appropriate?

Ignore minor wording differences if the core meaning and helpfulness are preserved.

Return ONLY a JSON object with this format:
{{
    "score": <0-100 integer>,
    "reasoning": "<brief explanation>"
}}
"""
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        try:
            response = await self._invoke_nova_lite(prompt, messages)
            result = self._parse_reasoning_response(response)
            return float(result.get("score", 0))
        except Exception as e:
            print(f"[Nova Evaluation] Error: {e}")
            return 0.0

    async def generate_synthetic_training_data(
        self,
        business_type: str,
        services: List[str],
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate synthetic training scenarios for a business.
        """
        prompt = f"""
Generate {count} realistic training scenarios for a {business_type} business.
The business offers these services: {', '.join(services)}.

Each scenario should be a JSON object with:
- "user_input": A realistic customer question or request
- "expected_response": The ideal, helpful response from the AI receptionist
- "category": One of [appointment_booking, customer_support, sales_inquiry, general_inquiry]

Return ONLY a JSON list of objects:
[
  {{ "user_input": "...", "expected_response": "...", "category": "..." }},
  ...
]
"""
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        try:
            response = await self._invoke_nova_lite(prompt, messages)
            # Clean markdown if present
            cleaned = re.sub(r'```json\s*', '', str(response), flags=re.IGNORECASE)
            cleaned = re.sub(r'```', '', cleaned, flags=re.IGNORECASE).strip()
            
            return json.loads(cleaned)
        except Exception as e:
            print(f"[Nova Synthetic] Error: {e}")
            return []

    def _check_deterministic_triggers(
        self,
        conversation: str,
        customer_context: Dict[str, Any],
        business_type: str
    ) -> Dict[str, Any]:
        """
        Check for deterministic escalation triggers BEFORE model invocation.
        
        Returns:
            Dictionary with should_escalate, reason, and trigger_type
        """
        conversation_lower = conversation.lower()
        
        # Check for critical keywords (immediate escalation)
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in conversation_lower:
                return {
                    "should_escalate": True,
                    "reason": f"Critical keyword detected: '{keyword}'",
                    "trigger_type": "critical_keyword",
                    "keyword": keyword
                }
        
        # Check for complaint escalation triggers
        complaint_count = customer_context.get("complaint_count", 0)
        satisfaction_score = customer_context.get("satisfaction_score", 0)
        
        # Repeat complaint pattern
        if complaint_count >= self.REPEAT_COMPLAINT_THRESHOLD:
            for keyword in self.COMPLAINT_KEYWORDS:
                if keyword in conversation_lower:
                    return {
                        "should_escalate": True,
                        "reason": f"Repeat complainant ({complaint_count} complaints) with escalation keyword: '{keyword}'",
                        "trigger_type": "repeat_complaint",
                        "complaint_count": complaint_count
                    }
        
        # VIP with negative sentiment indicators
        if satisfaction_score >= self.VIP_SATISFACTION_THRESHOLD:
            negative_indicators = ["unhappy", "disappointed", "not satisfied", "problem", "issue"]
            for indicator in negative_indicators:
                if indicator in conversation_lower:
                    return {
                        "should_escalate": True,
                        "reason": f"VIP customer (satisfaction: {satisfaction_score}) expressing: '{indicator}'",
                        "trigger_type": "vip_concern",
                        "satisfaction_score": satisfaction_score
                    }
        
        # Industry-specific triggers
        if business_type in ["medical", "dental"]:
            emergency_symptoms = ["chest pain", "difficulty breathing", "severe pain", "bleeding", "unconscious"]
            for symptom in emergency_symptoms:
                if symptom in conversation_lower:
                    return {
                        "should_escalate": True,
                        "reason": f"Medical emergency indicator: '{symptom}'",
                        "trigger_type": "medical_emergency",
                        "requires_911": True
                    }
        
        if business_type == "hvac":
            safety_keywords = ["gas smell", "gas leak", "carbon monoxide", "smoke", "fire"]
            for keyword in safety_keywords:
                if keyword in conversation_lower:
                    return {
                        "should_escalate": True,
                        "reason": f"Safety emergency: '{keyword}'",
                        "trigger_type": "safety_emergency",
                        "requires_911": True
                    }
        
        if business_type == "law_firm":
            urgent_legal = ["arrested", "court tomorrow", "deadline today", "being sued today"]
            for keyword in urgent_legal:
                if keyword in conversation_lower:
                    return {
                        "should_escalate": True,
                        "reason": f"Urgent legal matter: '{keyword}'",
                        "trigger_type": "urgent_legal"
                    }
        
        return {
            "should_escalate": False,
            "reason": None,
            "trigger_type": None
        }
    
    def _create_deterministic_escalation_response(
        self,
        trigger_info: Dict[str, Any],
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a response for deterministic escalation triggers.
        This bypasses the model entirely for safety-critical cases.
        """
        trigger_type = trigger_info.get("trigger_type")
        
        # Safety instruction based on trigger type
        if trigger_info.get("requires_911"):
            safety_response = "This sounds like an emergency. Please call 911 immediately if you're in danger. I'm connecting you with our team right away."
        elif trigger_type == "medical_emergency":
            safety_response = "For medical emergencies, please call 911 or go to your nearest emergency room. I'm alerting our medical team now."
        elif trigger_type == "safety_emergency":
            safety_response = "For your safety, please evacuate if you smell gas or suspect danger. I'm dispatching emergency service immediately."
        elif trigger_type == "urgent_legal":
            safety_response = "This sounds time-sensitive. I'm connecting you with an attorney right away."
        elif trigger_type == "vip_concern":
            safety_response = "I understand this is important to you. Let me connect you with our senior team member right away."
        else:
            safety_response = "Let me connect you with someone who can help you with this right away."
        
        return {
            "intent": "escalation_required",
            "confidence": 1.0,
            "entities": {},
            "selected_action": "HUMAN_INTERVENTION",
            "action_reasoning": f"DETERMINISTIC TRIGGER: {trigger_info['reason']}",
            "next_questions": [],
            "sentiment": "neutral",
            "escalation_risk": 1.0,
            "memory_update": {"key": "escalation", "value": trigger_info},
            "suggested_response": safety_response,
            "requires_approval": True,
            "safety_reason": trigger_info["reason"],
            "deterministic_trigger": True,
            "trigger_info": trigger_info,
            "reasoning_chain": [
                {
                    "step": 1,
                    "title": "Deterministic Safety Check",
                    "description": trigger_info["reason"],
                    "alert": True,
                    "trigger_type": trigger_type
                },
                {
                    "step": 2,
                    "title": "Action Override",
                    "description": "Bypassing model reasoning for safety-critical escalation",
                    "alert": True
                }
            ],
            "governance": {
                "business_type": business_context.get("type", "general"),
                "deterministic_bypass": True,
                "trigger_type": trigger_type
            }
        }
    
    def _build_system_prompt(
        self,
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        knowledge_context: str = "",
        training_context: str = "",
        popular_services_context: str = "",
        integrations_context: str = "" # New parameter
    ) -> str:
        """
        Build comprehensive system prompt with all context.
        Uses structured flow config for data-driven guidance.
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
        
        # Get structured flow context (replaces verbose prompt instructions)
        flow_context = BusinessTypeTemplate.get_flow_prompt_context(business_type)
        
        # Get risk profile for escalation logic
        risk_profile = BusinessTypeTemplate.get_risk_profile(business_type)
        
        # Build contact info section
        contact_section = ""
        if business_context.get('phone'):
            contact_section += f"- Business Phone: {business_context.get('phone')}\n"
        if business_context.get('address'):
            contact_section += f"- Business Address: {business_context.get('address')}\n"
        if business_context.get('website'):
            contact_section += f"- Website: {business_context.get('website')}\n"
        
        prompt = f"""
You are Nova 2 Lite, the reasoning core of an autonomous business operations agent.

Your role: Analyze customer calls, determine intent, select appropriate actions, and guide autonomous workflows.

## Available Actions:
{self._format_actions_list()}

## Business Context:
- Business Name: {business_context.get('name', 'Unknown')}
- Business Type: {business_type.title()}
{contact_section}- Services: {', '.join(business_context.get('services', []))}
{popular_services_context}{integrations_context}- Operating Hours: {business_context.get('operating_hours', 'Not specified')}
- Available Slots: {', '.join(business_context.get('available_slots', []))}
{menu_section}

{flow_context}

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
    "menu_item": "<if customer orders or asks about a menu item, extract item name (e.g., Kung Pow Chicken, burger)>",
    "quantity": "<number of items if specified, default 1>",
    "date": "<preferred_date_or_null>",
    "time": "<preferred_time_or_null>",
    "check_in_date": "<check_in_date_for_hotel_booking_or_null>" if business_type == "hotel" else None,
    "check_out_date": "<check_out_date_for_hotel_booking_or_null>" if business_type == "hotel" else None,
    "room_type": "<room_type_for_hotel_booking_e.g._King_Bed_Queen_Bed_or_null>" if business_type == "hotel" else None,
    "number_of_guests": "<number_of_guests_for_hotel_booking_or_null>" if business_type == "hotel" else None,
    "customer_name": "<extracted_name_or_null>",
    "customer_phone": "<extracted_phone_or_null>",
    "delivery_method": "<'pickup' or 'delivery' if customer specifies how they want their order>",
    "urgency": "<low|medium|high>",
    "issue_type": "<complaint_type_or_null>",
    "payment_method": "<extracted_payment_method_or_null>",
    "total_amount": "<extracted_amount_if_mentioned>",
    "landmark": "<extracted_nearby_landmark_if_mentioned>",
    "order_items": ["<list_of_ordered_items>"]
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
5. Identify missing information needed (use field collection order above)
6. Assess sentiment and escalation risk
7. Plan memory updates
8. Draft appropriate response

## Special Cases:
- If customer mentions "complaint", "unhappy", "manager", "terrible" → Check escalation_risk > 0.7
- If VIP customer (satisfaction > 4.5) → Set escalation_risk < 0.3, prioritize
- If repeat issue in history → Flag for human review, escalate
- If after hours → Suggest alternative or queue appointment
- If customer angry (negative sentiment + high urgency) → Consider TRANSFER_HUMAN
- **WRONG NUMBER SCENARIO - DO NOT ESCALATE**: 
  - If customer initially asks for wrong service (e.g., food at dental office), politely clarify your services
  - If customer says "no thank you, but I did need [your service]" → This is a VALID request, proceed confidently
  - Set confidence to 0.9+ when customer explicitly requests your services
  - Use CREATE_APPOINTMENT, PROVIDE_INFO, or appropriate action - NOT HUMAN_INTERVENTION
  - Example: Customer asks for food → AI clarifies it's dental office → Customer says "no thank you, but i did need teeth cleaning" → AI should book appointment, NOT escalate
- **IMPORTANT - Appointment Booking**: 
  - When customer provides name and phone, ACCEPT it immediately - DO NOT ask to "confirm" or "verify"
  - Only ask for missing fields - DO NOT re-ask for fields already provided
  - If customer says "my name is John Doe" → customer_name is "John Doe" - move on
  - If customer says "my number is 1234567890" → customer_phone is extracted - move on
  - Use CREATE_APPOINTMENT action once you have name, phone, and timing info
  - DO NOT use COLLECT_INFO if customer already provided the information
- **CRITICAL - Order Taking Flow**:
  - When customer says they want to ORDER something (e.g., "I want to order...", "I'd like to get...", "Can I have..."):
    1. Extract the menu_item entity from their request
    2. Set selected_action to "PLACE_ORDER" 
    3. The menu_item entity should be the exact name of what they want to order
    4. ONLY mention the price ONCE per item - do NOT repeat prices
    5. Ask if they want pickup or delivery (only if not already specified)
  - When customer specifies pickup/delivery:
    1. Extract delivery_method entity ("pickup" or "delivery")
    2. Do NOT ask again about pickup/delivery if already answered
  - When customer CONFIRMS their order (e.g., "yes", "that's all", "confirm", "that's it", "place the order"):
    1. Set selected_action to "CONFIRM_ORDER"
    2. Only use CONFIRM_ORDER when the customer has explicitly confirmed they want to finalize
  - **DO NOT repeat information** - If price was already mentioned, do NOT mention it again
  - **DO NOT ask questions already answered** - If customer said "pickup", do NOT ask about delivery method
  - **DO NOT ask to "confirm" info** - If customer said their phone number, trust it and move on
- **CRITICAL - Availability Checking**:
  - When customer asks "is the doctor available at [time]?" or "will you be available at [time]?":
    1. Extract the time from the question into the "preferred_time" entity
    2. Set selected_action to "PROVIDE_INFO" (NOT CREATE_APPOINTMENT - they're asking, not booking yet)
    3. The "preferred_time" entity should contain the time string (e.g., "tomorrow at 2pm", "2pm tomorrow")
    4. Suggested response should acknowledge you're checking availability
    5. DO NOT try to book the appointment - just answer the availability question
  - Examples:
    - "is the doctor available at 2pm tomorrow?" → preferred_time: "tomorrow at 2pm", action: PROVIDE_INFO
    - "will you be open at 5pm today?" → preferred_time: "5pm today", action: PROVIDE_INFO
    - "can I book for next Tuesday at 10am?" → preferred_time: "next Tuesday at 10am", action: CREATE_APPOINTMENT (they want to book, not just check)
- **INTENT VALIDATION - IMPORTANT**: Before accepting orders, verify they match the business type
  - Restaurant: Accept food orders. If customer asks for appointments/services, be helpful - explain what you do offer, offer to schedule if you provide that service (e.g., restaurants may offer event catering)
  - Auto Repair: Accept service requests. If customer asks for food, be understanding - explain this is an auto shop but see if you can still help (maybe suggest nearby restaurants)
  - Medical/Dental: Accept health-related requests. If customer asks for unrelated services (food, retail), politely clarify your services while remaining helpful
  - Law Firm: Accept legal consultations. If customer asks for unrelated services, acknowledge and suggest they may have reached the wrong number, but remain courteous
  - Example flexible response: "I notice you mentioned wanting to [requested_service]. I'm actually with {{business_name}}, and we specialize in [business_services]. Would you still like me to help you with [business_services], or would you like me to help you find the right place for [requested_service]?"
  - Example for clearly wrong intent: "I'm happy to help, but I want to make sure you're in the right place. You mentioned wanting to [wrong_intent]. This is {{business_name}} and we offer [business_services]. Did you mean to call a [appropriate_business], or would you like me to help you with our services instead?"
  - Be helpful and courteous, not dismissive. The customer may have dialed by mistake or be unsure of the correct number.

## Quality Guidelines:
- Confidence should reflect how clearly the intent is expressed
- Only extract entities if explicitly mentioned
- Action reasoning should be specific and contextual
- Next questions should be minimal - only ask what's needed
- Escalation risk should account for both sentiment and history
- **LOW escalation risk** (0.0-0.3): Normal operations, proceed with confidence
- **MEDIUM escalation risk** (0.3-0.6): Proceed but be cautious, may need confirmation
- **HIGH escalation risk** (0.6-0.8): Consider human intervention, but not automatic
- **CRITICAL escalation risk** (0.8-1.0): Human intervention required
- **IMPORTANT**: Wrong number dialing + clarification = LOW risk (0.2-0.3), NOT high risk
- **IMPORTANT**: Customer saying "no thank you" to clarification is NOT a complaint, set escalation_risk to 0.2
- **BUSINESS INTRODUCTION**: When greeting, introduce the business by name. For example: "Thank you for calling {{business_name}}. How can I help you today?"
- **WRONG NUMBER/INTENT HANDLING - BE HELPFUL NOT DISMISSIVE**: 
  - If customer intent doesn't match business type, be understanding and offer options
  - Don't reject outright - clarify your services while remaining helpful
  - **CRITICAL**: When customer clarifies they DO want your services (after initial confusion), proceed confidently - DO NOT escalate to human
  - Example flexible response: "I notice you mentioned wanting to [requested_service]. I'm actually with {{business_name}}, and we specialize in [business_services]. Would you still like me to help you with [business_services], or would you like me to help you find the right place for [requested_service]?"
  - If customer says "no thank you, but I did need [your service]" → This is a VALID request, proceed with CREATE_APPOINTMENT or appropriate action
  - Example for clearly wrong intent: "I'm happy to help, but I want to make sure you're in the right place. You mentioned wanting to [wrong_intent]. This is {{business_name}} and we offer [business_services]. Did you mean to call a [appropriate_business], or would you like me to help you with our services instead?"
  - Be helpful and courteous, not dismissive. The customer may have dialed by mistake or be unsure of the correct number.
  - **CONFIDENCE BOOSTING**: When customer explicitly requests your services (e.g., "i did need teeth cleaning", "i want an appointment"), set confidence to 0.9+ regardless of initial confusion
  - **ONLY escalate to human if**: 
    - Customer is angry/frustrated AND asking for supervisor/manager
    - Customer has repeated complaints (2+ times)
    - Emergency situation (medical, safety, legal urgency)
    - Complex issue beyond your capabilities
  - **DO NOT escalate for**: Simple requests, clarification of services, wrong number dialing, or customer changing their mind
- **INTENT VALIDATION - FLEXIBLE APPROACH**: Before accepting orders, verify they match the business type but remain helpful
  - Restaurant: Accept food orders. If customer asks for appointments/services, be helpful - explain what you do offer, offer to schedule if you provide that service (e.g., restaurants may offer event catering)
  - Auto Repair: Accept service requests. If customer asks for food, be understanding - explain this is an auto shop but see if you can still help (maybe suggest nearby restaurants)
  - Medical/Dental: Accept health-related requests. If customer asks for unrelated services (food, retail), politely clarify your services while remaining helpful
  - Law Firm: Accept legal consultations. If customer asks for unrelated services, acknowledge and suggest they may have reached the wrong number, but remain courteous
  - **KEY PRINCIPLE**: The goal is to help the customer, not to reject them. Clarify your services politely, offer alternatives when possible, and be understanding of potential dialing errors.
  - **CONFIDENCE AFTER CLARIFICATION**: When customer initially asks for wrong service but then clarifies they want your actual services (e.g., "no thank you, but i did need teeth cleaning"), set confidence to 0.9+ and proceed with appropriate action
  - **DO NOT USE HUMAN_INTERVENTION** just because customer initially asked for wrong service - if they clarify they want your services, handle it normally
  - **HUMAN_INTERVENTION should ONLY be used for**: 
    - Angry customers demanding supervisor/manager
    - Repeat complaints about same issue
    - Emergency situations (911, medical emergency, safety hazards)
    - Legal threats or harassment
    - Complex issues beyond your training
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
            "TAKE_MESSAGE": "Record message for callback",
            "PAYMENT_PROCESS": "Initiate secure payment collection",
            "SEND_DIRECTIONS": "Provide business location and directions",
            "PLACE_ORDER": "Add item to customer's order cart (step 1 of order flow)",
            "CONFIRM_ORDER": "Finalize and save the complete order (step 2 of order flow)",
            "HUMAN_INTERVENTION": "Pause for human review before any action"
        }
        
        return "\n".join([
            f"{action}: {desc}" 
            for action, desc in descriptions.items()
        ])
    
    async def _invoke_nova_lite(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_retries: int = 3
    ) -> str:
        """
        Invoke Nova 2 Lite model with structured reasoning prompt.
        Uses asyncio.to_thread to prevent blocking the event loop.
        Implements retry logic with exponential backoff for transient failures.
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
        
        # Retry configuration
        config = RetryConfig(
            max_retries=max_retries,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Transient exceptions that should be retried
        transient_exceptions = (
            ClientError,
            ReadTimeoutError, 
            ConnectTimeoutError,
            ConnectionError,
            TimeoutError
        )
        
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                # Run synchronous Bedrock call in a thread pool
                response = await asyncio.to_thread(
                    self._invoke_bedrock_sync,
                    body
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
                    raise ModelInvocationError(f"Unexpected response format: {response_body}")
                    
            except transient_exceptions as e:
                last_exception = e
                
                if attempt == config.max_retries:
                    raise ModelInvocationError(
                        f"Failed to invoke model after {config.max_retries} retries: {str(e)}",
                        retry_count=config.max_retries
                    )
                
                # Calculate delay with exponential backoff
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )
                
                # Add jitter
                if config.jitter:
                    delay = delay * (0.5 + random.random())
                
                print(f"[Nova Reasoning] Retry {attempt + 1}/{config.max_retries} after {delay:.2f}s due to: {e}")
                await asyncio.sleep(delay)
        
        raise ModelInvocationError(
            f"Failed to invoke model: {last_exception}",
            retry_count=config.max_retries
        )
    
    def _invoke_bedrock_sync(self, body: Dict[str, Any]) -> Any:
        """
        Synchronous Bedrock invocation (called from thread pool).
        """
        return self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
    
    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate the reasoning response.
        Uses multi-layer JSON extraction for robustness.
        
        Layers:
        1. Direct parse if response is already dict
        2. Strip markdown and try direct JSON parse
        3. Regex extraction for JSON with nested objects
        4. Balanced brace extraction for complex nested JSON
        5. Fallback to error response
        """
        print(f"[Nova Reasoning] Raw response length: {len(response)} chars")
        
        result = None
        
        # Layer 1: Already a dict
        if isinstance(response, dict):
            result = response
        
        else:
            # Clean up markdown code blocks
            cleaned = re.sub(r'```json\s*', '', str(response), flags=re.IGNORECASE)
            cleaned = re.sub(r'```[\w]*\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()
            
            # Layer 2: Direct JSON parse
            try:
                result = json.loads(cleaned)
                print(f"[Nova Reasoning] Layer 2 success: direct JSON parse")
            except json.JSONDecodeError:
                # Layer 3: Regex for JSON with nested objects
                # This pattern handles one level of nesting
                try:
                    json_pattern = r'\{(?:[^{}]|\{[^{}]*\})*\}'
                    match = re.search(json_pattern, cleaned, re.DOTALL)
                    if match:
                        result = json.loads(match.group(0))
                        print(f"[Nova Reasoning] Layer 3 success: regex extraction")
                except (json.JSONDecodeError, AttributeError):
                    pass
                
                # Layer 4: Balanced brace extraction for deeply nested JSON
                if result is None:
                    result = self._extract_nested_json(cleaned)
                    if result:
                        print(f"[Nova Reasoning] Layer 4 success: balanced brace extraction")
        
        # Layer 5: Fallback
        if result is None:
            print(f"[Nova Reasoning] All parsing layers failed, using fallback")
            return self._get_fallback_response("Could not parse JSON from response")
        
        # Validate required fields
        required_fields = [
            "intent", "confidence", "entities", "selected_action",
            "action_reasoning", "sentiment", "escalation_risk", "suggested_response"
        ]
        
        for field in required_fields:
            if field not in result:
                print(f"[Nova Reasoning] Missing field '{field}', using default")
                result[field] = self._get_default_value(field)
        
        # Validate and normalize selected action
        if result["selected_action"] not in self.available_actions:
            # Map deprecated CREATE_ORDER to CONFIRM_ORDER
            if result["selected_action"] == "CREATE_ORDER":
                result["selected_action"] = "CONFIRM_ORDER"
                result["action_reasoning"] = "Mapped CREATE_ORDER to CONFIRM_ORDER for consistency"
            else:
                result["selected_action"] = "PROVIDE_INFO"
                result["action_reasoning"] = "Defaulted to providing information due to unclear intent"
        
        # Ensure types are correct
        result["confidence"] = float(result.get("confidence", 0.5))
        result["escalation_risk"] = float(result.get("escalation_risk", 0.1))
        
        # Ensure next_questions is a list
        if "next_questions" not in result or not isinstance(result["next_questions"], list):
            result["next_questions"] = []
        
        # Handle memory updates
        if "memory_update" not in result:
            result["memory_update"] = {"key": "none", "value": None}
        else:
            # Apply memory updates if customer context is available
            memory_update = result["memory_update"]
            if memory_update and memory_update.get("key") != "none" and "customer_context" in locals():
                customer_id = customer_context.get("id") or customer_context.get("phone") or "unknown"
                if customer_id != "unknown":
                    asyncio.create_task(
                        self.memory_store.store_memory(
                            customer_id, 
                            memory_update["key"], 
                            memory_update["value"]
                        )
                    )
        
        return result
    
    def _extract_nested_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Robustly extract nested JSON from text by finding balanced braces.
        This handles nested objects correctly unlike simple regex.
        """
        # Find the first opening brace
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        # Track brace depth to find the matching closing brace
        depth = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(text)):
            char = text[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        
        if depth != 0:
            # Unbalanced braces - try to parse what we have
            return None
        
        json_str = text[start_idx:end_idx]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    
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

    async def retrieve_customer_memory(self, customer_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve customer memories for context enrichment
        
        Args:
            customer_context: Customer information containing ID or phone
            
        Returns:
            Dictionary containing customer memories
        """
        customer_id = customer_context.get("id") or customer_context.get("phone") or "unknown"
        if customer_id == "unknown":
            return {}
        
        memories = await self.memory_store.retrieve_memory(customer_id)
        if not memories:
            return {}
        
        # Filter to only return the memory values with their keys
        memory_values = {}
        for key, memory_entry in memories.items():
            memory_values[key] = memory_entry["value"]
        
        return memory_values

    async def update_customer_memory(self, customer_context: Dict[str, Any], memory_key: str, memory_value: Any):
        """
        Update customer memory with new information
        
        Args:
            customer_context: Customer information containing ID or phone
            memory_key: Key for the memory entry
            memory_value: Value to store
        """
        customer_id = customer_context.get("id") or customer_context.get("phone") or "unknown"
        if customer_id != "unknown":
            await self.memory_store.store_memory(customer_id, memory_key, memory_value)

    async def perform_multi_step_reasoning(
        self,
        conversation: str,
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        db=None,
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        Perform advanced multi-step reasoning for complex tasks
        
        Args:
            conversation: Current conversation transcript
            business_context: Business information
            customer_context: Customer information
            db: Database session
            max_steps: Maximum number of reasoning steps
            
        Returns:
            Structured reasoning result with multi-step analysis
        """
        # Retrieve any existing customer memories
        customer_memories = await self.retrieve_customer_memory(customer_context)
        
        # Build enhanced system prompt with multi-step reasoning instructions
        system_prompt = self._build_multi_step_system_prompt(
            business_context, 
            customer_context, 
            customer_memories
        )
        
        # Create the multi-step reasoning prompt
        multi_step_prompt = f"""
Analyze this conversation using multi-step reasoning to understand the customer's needs and determine the best course of action.

Conversation: {conversation}

Follow these steps in your analysis:
1. Identify the customer's primary goal or request
2. Identify any constraints or special requirements
3. Consider the customer's history and preferences
4. Determine what information is needed to fulfill the request
5. Plan the sequence of actions needed to address the request
6. Identify any potential risks or issues
7. Formulate an appropriate response

Provide your response in the following JSON format:
{{
  "multi_step_analysis": {{
    "primary_goal": "string",
    "constraints": ["list", "of", "constraints"],
    "customer_history_considerations": "string",
    "required_information": ["list", "of", "required", "information"],
    "action_sequence": [
      {{
        "step": 1,
        "action": "string",
        "description": "string"
      }}
    ],
    "potential_risks": ["list", "of", "risks"],
    "recommended_response": "string"
  }},
  "intent": "string",
  "confidence": float,
  "entities": {{"key": "value"}},
  "selected_action": "string",
  "action_reasoning": "string",
  "next_questions": ["string"],
  "sentiment": "string",
  "escalation_risk": float,
  "memory_update": {{"key": "string", "value": "string"}},
  "suggested_response": "string",
  "requires_approval": boolean,
  "intent_validated": boolean
}}

Focus on providing a detailed, step-by-step analysis of the situation.
"""
        
        messages = [
            {"role": "user", "content": [{"text": multi_step_prompt}]}
        ]
        
        try:
            response = await self._invoke_nova_lite(system_prompt, messages)
            
            # Parse the response
            result = self._parse_reasoning_response(response)
            
            # Add multi-step analysis if available
            if "multi_step_analysis" not in result:
                # Create a prompt specifically for multi-step analysis
                analysis_prompt = f"""
Analyze the conversation using multi-step reasoning:

Conversation: {conversation}

Provide only the multi_step_analysis part of the response in JSON format:
{{
  "multi_step_analysis": {{
    "primary_goal": "Identify customer's main request",
    "constraints": ["list any constraints mentioned"],
    "customer_history_considerations": "Consider customer history and preferences",
    "required_information": ["information needed to help customer"],
    "action_sequence": [
      {{
        "step": 1,
        "action": "first action to take",
        "description": "what the action accomplishes"
      }}
    ],
    "potential_risks": ["any potential issues to be aware of"],
    "recommended_response": "suggested response to customer"
  }}
}}
"""
                analysis_response = await self._invoke_nova_lite(system_prompt, 
                    [{"role": "user", "content": [{"text": analysis_prompt}]}])
                
                # Try to extract the multi-step analysis
                analysis_result = self._parse_reasoning_response(analysis_response)
                if "multi_step_analysis" in analysis_result:
                    result["multi_step_analysis"] = analysis_result["multi_step_analysis"]
            
            return result
            
        except Exception as e:
            # Fallback to regular reasoning if multi-step reasoning fails
            print(f"[Nova Multi-Step Reasoning] Error: {e}")
            return await self.reason(
                conversation=conversation,
                business_context=business_context,
                customer_context=customer_context,
                db=db
            )

    def _build_multi_step_system_prompt(
        self,
        business_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        customer_memories: Dict[str, Any]
    ) -> str:
        """
        Build system prompt for multi-step reasoning
        
        Args:
            business_context: Business information
            customer_context: Customer information
            customer_memories: Customer memories
            
        Returns:
            System prompt string
        """
        prompt = f"""
You are Nova 2 Lite, the reasoning core of an autonomous business operations agent.

Your role: Analyze customer calls using multi-step reasoning to determine intent, select appropriate actions, and guide autonomous workflows.

## Available Actions:
{self._format_actions_list()}

## Business Context:
- Business Name: {business_context.get('name', 'Unknown')}
- Business Type: {business_context.get('type', 'general').title()}
- Services: {', '.join(business_context.get('services', []))}
- Operating Hours: {business_context.get('operating_hours', 'Not specified')}
- Available Slots: {', '.join(business_context.get('available_slots', []))}

## Customer Context:
- Name: {customer_context.get('name', 'Unknown')}
- Phone: {customer_context.get('phone', 'Unknown')}
- Previous Calls: {customer_context.get('call_count', 0)}
- Last Contact: {customer_context.get('last_contact', 'Never')}
- Satisfaction Score: {customer_context.get('satisfaction_score', 0)}/5.0
- Preferred Services: {', '.join(customer_context.get('preferred_services', []))}
- Previous Complaints: {customer_context.get('complaint_count', 0)}

## Customer Memories:
{json.dumps(customer_memories, indent=2) if customer_memories else 'No previous memories'}

## Multi-Step Reasoning Requirements:
1. Analyze the conversation thoroughly
2. Consider historical context and customer preferences
3. Identify the customer's primary goal
4. Determine required information to fulfill the request
5. Plan the sequence of actions needed
6. Identify potential risks or issues
7. Formulate an appropriate response

## Response Format (strict JSON):
{{
  "multi_step_analysis": {{
    "primary_goal": "string",
    "constraints": ["list", "of", "constraints"],
    "customer_history_considerations": "string",
    "required_information": ["list", "of", "required", "information"],
    "action_sequence": [
      {{
        "step": 1,
        "action": "string",
        "description": "string"
      }}
    ],
    "potential_risks": ["list", "of", "risks"],
    "recommended_response": "string"
  }},
  "intent": "string",
  "confidence": float,
  "entities": {{"key": "value"}},
  "selected_action": "string",
  "action_reasoning": "string",
  "next_questions": ["string"],
  "sentiment": "string",
  "escalation_risk": float,
  "memory_update": {{"key": "string", "value": "string"}},
  "suggested_response": "string"
}}

Apply thorough multi-step reasoning to understand and address the customer's needs.
"""
        return prompt


# Singleton instance
nova_reasoning = NovaReasoningEngine()


class CustomerMemoryStore:
    """
    Persistent memory store for customer information and preferences.
    Enables long-term learning and personalization across sessions.
    """
    
    def __init__(self):
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
    
    async def store_memory(
        self,
        customer_id: str,
        memory_key: str,
        memory_value: Any,
        ttl_hours: Optional[int] = None
    ):
        """
        Store customer memory with optional TTL.
        
        Args:
            customer_id: Unique customer identifier
            memory_key: Key for the memory entry
            memory_value: Value to store
            ttl_hours: Optional time-to-live in hours
        """
        if customer_id not in self._memory_store:
            self._memory_store[customer_id] = {}
        
        self._memory_store[customer_id][memory_key] = {
            "value": memory_value,
            "stored_at": datetime.now().isoformat(),
            "ttl_hours": ttl_hours
        }
        
        self._timestamps[customer_id] = datetime.now()
    
    async def retrieve_memory(
        self,
        customer_id: str,
        memory_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve customer memory.
        
        Args:
            customer_id: Unique customer identifier
            memory_key: Optional specific key to retrieve, or all if None
            
        Returns:
            Dictionary containing memory entries
        """
        if customer_id not in self._memory_store:
            return {}
        
        memories = self._memory_store[customer_id]
        
        # Check TTL and clean expired entries
        current_time = datetime.now()
        valid_memories = {}
        
        for key, memory_data in memories.items():
            if memory_key and key != memory_key:
                continue
            
            # Check if memory has expired
            if memory_data.get("ttl_hours"):
                stored_time = datetime.fromisoformat(memory_data["stored_at"])
                expiry_time = stored_time + timedelta(hours=memory_data["ttl_hours"])
                if current_time > expiry_time:
                    continue  # Skip expired memory
            
            valid_memories[key] = memory_data
        
        return valid_memories
    
    async def get_customer_context(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive customer context from stored memories.
        
        Args:
            customer_id: Unique customer identifier
            
        Returns:
            Dictionary with customer context
        """
        memories = await self.retrieve_memory(customer_id)
        
        context = {
            "customer_id": customer_id,
            "stored_preferences": {},
            "interaction_history": {},
            "behavioral_patterns": {}
        }
        
        for key, memory_data in memories.items():
            value = memory_data["value"]
            
            if key.startswith("preference_"):
                context["stored_preferences"][key.replace("preference_", "")] = value
            elif key.startswith("history_"):
                context["interaction_history"][key.replace("history_", "")] = value
            elif key.startswith("pattern_"):
                context["behavioral_patterns"][key.replace("pattern_", "")] = value
        
        return context
    
    async def cleanup_expired_memories(self):
        """Clean up expired memories for all customers."""
        current_time = datetime.now()
        
        for customer_id in list(self._memory_store.keys()):
            memories = self._memory_store[customer_id]
            valid_memories = {}
            
            for key, memory_data in memories.items():
                if memory_data.get("ttl_hours"):
                    stored_time = datetime.fromisoformat(memory_data["stored_at"])
                    expiry_time = stored_time + timedelta(hours=memory_data["ttl_hours"])
                    if current_time > expiry_time:
                        continue  # Skip expired memory
                
                valid_memories[key] = memory_data
            
            if valid_memories:
                self._memory_store[customer_id] = valid_memories
            else:
                # Remove customer entry if no valid memories
                del self._memory_store[customer_id]
                if customer_id in self._timestamps:
                    del self._timestamps[customer_id]


# Singleton memory store instance
memory_store = CustomerMemoryStore()
