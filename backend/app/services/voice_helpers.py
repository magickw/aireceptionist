"""
Voice Helpers — shared pure functions used by both WebSocket and HTTP handlers.

These functions operate on a session dict (either ws_session or http_session)
and return values without side effects (no WebSocket sends, no DB writes).
"""
import re
import array
import struct
from typing import Dict, Any, Optional, Tuple, List

from app.core.logging import get_logger

logger = get_logger("voice_helpers")


# ── Audio conversion utilities (for Twilio integration) ────────────────


def mulaw_to_pcm16(mulaw_bytes: bytes) -> bytes:
    """
    Convert 8kHz mulaw audio to 16kHz PCM16.
    
    Twilio sends mulaw at 8kHz, but Nova expects PCM16 at 16kHz.
    This does two things:
    1. Decode mulaw to 16-bit PCM
    2. Resample from 8kHz to 16kHz (linear interpolation)
    
    Args:
        mulaw_bytes: Raw mulaw-encoded audio bytes at 8kHz
        
    Returns:
        PCM16 audio bytes at 16kHz (little-endian)
    """
    # Mulaw lookup table (standard ITU-T G.711)
    MULAW_TABLE = [
        -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
        -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
        -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
        -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
        -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
        -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
        -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
        -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
        -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
        -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
        -876, -844, -812, -780, -748, -716, -684, -652,
        -620, -588, -556, -524, -492, -460, -428, -396,
        -372, -356, -340, -324, -308, -292, -276, -260,
        -244, -228, -212, -196, -180, -164, -148, -132,
        -120, -112, -104, -96, -88, -80, -72, -64,
        -56, -48, -40, -32, -24, -16, -8, 0,
        32124, 31100, 30076, 29052, 28028, 27004, 25980, 24956,
        23932, 22908, 21884, 20860, 19836, 18812, 17788, 16764,
        15996, 15484, 14972, 14460, 13948, 13436, 12924, 12412,
        11900, 11388, 10876, 10364, 9852, 9340, 8828, 8316,
        7932, 7676, 7420, 7164, 6908, 6652, 6396, 6140,
        5884, 5628, 5372, 5116, 4860, 4604, 4348, 4092,
        3900, 3772, 3644, 3516, 3388, 3260, 3132, 3004,
        2876, 2748, 2620, 2492, 2364, 2236, 2108, 1980,
        1884, 1820, 1756, 1692, 1628, 1564, 1500, 1436,
        1372, 1308, 1244, 1180, 1116, 1052, 988, 924,
        876, 844, 812, 780, 748, 716, 684, 652,
        620, 588, 556, 524, 492, 460, 428, 396,
        372, 356, 340, 324, 308, 292, 276, 260,
        244, 228, 212, 196, 180, 164, 148, 132,
        120, 112, 104, 96, 88, 80, 72, 64,
        56, 48, 40, 32, 24, 16, 8, 0,
    ]
    
    if not mulaw_bytes:
        return b''
    
    # Step 1: Decode mulaw to 16-bit PCM
    pcm16_8khz = array.array('h', [MULAW_TABLE[b] for b in mulaw_bytes])
    
    # Step 2: Resample from 8kHz to 16kHz (simple linear interpolation)
    # We need 2 output samples for every 1 input sample
    pcm16_16khz = array.array('h', [0] * (len(pcm16_8khz) * 2))
    
    for i in range(len(pcm16_8khz) - 1):
        sample1 = pcm16_8khz[i]
        sample2 = pcm16_8khz[i + 1]
        
        # Linear interpolation
        pcm16_16khz[i * 2] = sample1
        pcm16_16khz[i * 2 + 1] = (sample1 + sample2) // 2
    
    # Handle last sample
    if pcm16_8khz:
        pcm16_16khz[-2] = pcm16_8khz[-1]
        pcm16_16khz[-1] = pcm16_8khz[-1]
    
    return pcm16_16khz.tobytes()


def pcm16_to_mulaw(pcm16_bytes: bytes) -> bytes:
    """
    Convert 16kHz PCM16 audio to 8kHz mulaw.
    
    Nova generates PCM16 at 16kHz, but Twilio expects mulaw at 8kHz.
    This does two things:
    1. Resample from 16kHz to 8kHz (downsampling)
    2. Encode to mulaw
    
    Args:
        pcm16_bytes: PCM16 audio bytes at 16kHz (little-endian)
        
    Returns:
        Mulaw-encoded audio bytes at 8kHz
    """
    # Inverse mulaw lookup table (approximate)
    PCM16_TO_MULAW = {}
    # Build a simplified inverse lookup (this is an approximation)
    for i, val in enumerate([
        -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
        -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
        -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
        -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
        -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
        -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
        -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
        -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
        -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
        -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
        -876, -844, -812, -780, -748, -716, -684, -652,
        -620, -588, -556, -524, -492, -460, -428, -396,
        -372, -356, -340, -324, -308, -292, -276, -260,
        -244, -228, -212, -196, -180, -164, -148, -132,
        -120, -112, -104, -96, -88, -80, -72, -64,
        -56, -48, -40, -32, -24, -16, -8, 0,
    ]):
        PCM16_TO_MULAW[val] = i
    
    if not pcm16_bytes:
        return b''
    
    # Step 1: Decode PCM16 bytes to integers
    pcm16_array = array.array('h')
    pcm16_array.frombytes(pcm16_bytes)
    
    # Step 2: Downsample from 16kHz to 8kHz (take every other sample)
    pcm16_8khz = pcm16_array[::2]
    
    # Step 3: Encode to mulaw
    mulaw_bytes = bytes()
    for sample in pcm16_8khz:
        # Find closest value in lookup table
        mulaw_index = PCM16_TO_MULAW.get(sample, 0)
        # Invert the bits for standard mulaw encoding
        mulaw_bytes += bytes([~mulaw_index & 0xFF])
    
    return mulaw_bytes


# ── Customer info extraction ────────────────────────────────────────────

_PHONE_PATTERNS = [
    re.compile(r'(?:phone|number|cell|mobile|call|reach)[\s:]*([+]?\d[\d\s\-\(\)]{8,})', re.IGNORECASE),
    re.compile(r'\b(\d{3}[\s\-]?\d{3}[\s\-]?\d{4})\b'),
    re.compile(r'\b(\d{10,11})\b'),
]

_NAME_PATTERNS = [
    re.compile(r"(?:name is|i am|call me|this is|my name's)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE),
    re.compile(r"(?:name is|i am|call me|this is|my name's)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", re.IGNORECASE),
]


def extract_customer_info(
    text: str,
    entities: Dict[str, Any],
    session: Dict[str, Any],
) -> Dict[str, Optional[str]]:
    """
    Extract customer name and phone from entities or message text.
    Updates *session* in place and returns ``{"name": ..., "phone": ...}``.
    """
    name = entities.get("customer_name")
    phone = entities.get("customer_phone")

    if not phone and text:
        for pat in _PHONE_PATTERNS:
            m = pat.search(text)
            if m:
                cleaned = re.sub(r'[^\d]', '', m.group(1))
                if len(cleaned) >= 10:
                    phone = cleaned
                    break

    if not name and text:
        for pat in _NAME_PATTERNS:
            m = pat.search(text)
            if m:
                name = m.group(1).title()
                break

    if name:
        session["customer_name"] = name
    if phone:
        session["customer_phone"] = phone

    return {"name": name, "phone": phone}


# ── Confirmation keywords ───────────────────────────────────────────────

_CONFIRM_KW = ["yes", "yeah", "yep", "sure", "please", "book", "confirm", "go ahead", "do it", "ok", "okay"]
_DECLINE_KW = ["no", "nah", "cancel", "don't", "different", "other", "change", "another"]


def check_confirmation_keywords(msg_lower: str) -> Tuple[bool, bool]:
    """Return ``(confirms, declines)`` based on keyword matching."""
    confirms = any(kw in msg_lower for kw in _CONFIRM_KW) and not any(kw in msg_lower for kw in _DECLINE_KW)
    declines = any(kw in msg_lower for kw in _DECLINE_KW)
    return confirms, declines


# ── Pending appointment ─────────────────────────────────────────────────

async def handle_pending_appointment(
    session: Dict[str, Any],
    msg_lower: str,
    reasoning_result: Dict[str, Any],
    business_id: int,
    db: Any,
) -> Optional[Dict[str, Any]]:
    """
    If there is a ``pending_appointment`` in session and the user confirms or
    declines, process it.

    Returns ``{"response": str, "confirmed": bool}`` when handled, or ``None``.
    """
    pending = session.get("pending_appointment")
    if not pending:
        return None

    # Prefer model action over keywords (Item 8)
    selected_action = reasoning_result.get("selected_action", "")
    if selected_action in ("CONFIRM_APPOINTMENT", "BOOK_APPOINTMENT"):
        confirms, declines = True, False
    elif selected_action in ("CANCEL_APPOINTMENT", "RESCHEDULE"):
        confirms, declines = False, True
    else:
        confirms, declines = check_confirmation_keywords(msg_lower)

    if not confirms and not declines:
        return None

    if confirms:
        session.pop("pending_appointment")
        try:
            from app.services.calendar_service import calendar_service
            result = await calendar_service.check_and_book_appointment(
                business_id=business_id,
                start_time=pending["start_time"],
                end_time=pending["end_time"],
                customer_name=session.get("customer_name", "Unknown"),
                customer_phone=session.get("customer_phone", "Unknown"),
                service=pending.get("service", "General Checkup"),
                db=db,
            )
            if result["success"]:
                date_fmt = pending["start_time"].strftime("%B %d")
                time_fmt = pending["start_time"].strftime("%I:%M %p")
                session["appointment_confirmed"] = True
                session["last_appointment_summary"] = {
                    "start_time": pending["start_time"],
                    "end_time": pending["end_time"],
                    "service": pending.get("service", "General Checkup"),
                }
                return {"response": f"Great! I've booked your appointment for {date_fmt} at {time_fmt}. We'll see you then!", "confirmed": True}
            else:
                return {"response": f"I'm sorry, I couldn't book that appointment. {result.get('message', 'Please try a different time.')}", "confirmed": False}
        except Exception:
            return {"response": "I'm having trouble booking that appointment right now. Could you please try again?", "confirmed": False}

    # user declines
    session.pop("pending_appointment", None)
    return {"response": "No problem! Would you like to check a different time?", "confirmed": False}


# ── Gratitude / closing detection ────────────────────────────────────────

_GRATITUDE = ["thank you", "thanks", "thank", "thx", "appreciate it"]
_CLOSING = ["bye", "goodbye", "good bye", "see you", "take care", "have a nice", "have a great", "talk to you later"]


def detect_gratitude_closing(msg_lower: str) -> Tuple[bool, bool]:
    """Return ``(is_gratitude, is_closing)``."""
    is_gratitude = any(p in msg_lower for p in _GRATITUDE)
    is_closing = any(p in msg_lower for p in _CLOSING)
    return is_gratitude, is_closing


def check_task_completed(session: Dict[str, Any], response: str) -> bool:
    """Check if a task was recently completed."""
    return bool(
        session.get("order_confirmed")
        or session.get("appointment_confirmed")
        or "booked your appointment" in response
        or "confirmed your order" in response
    )


def build_gratitude_response(session: Dict[str, Any]) -> str:
    """Build response for gratitude after task completion."""
    if session.get("order_confirmed"):
        last_order = session.get("last_order_summary", {})
        if last_order:
            return f"You're welcome! Your order ({last_order.get('items', 'your items')}) will be ready for {last_order.get('delivery_method', 'pickup')}. Have a great day!"
    if session.get("appointment_confirmed"):
        last_appt = session.get("last_appointment_summary", {})
        if last_appt and last_appt.get("start_time"):
            date_fmt = last_appt["start_time"].strftime("%B %d")
            time_fmt = last_appt["start_time"].strftime("%I:%M %p")
            return f"You're welcome! We'll see you on {date_fmt} at {time_fmt}. Have a wonderful day!"
    return "You're welcome! Is there anything else I can help you with?"


def build_closing_response(session: Dict[str, Any]) -> str:
    """Build response for closing phrases after task completion."""
    if session.get("order_confirmed"):
        return "Thank you for your order! Have a great day, and we look forward to serving you again soon!"
    if session.get("appointment_confirmed"):
        return "Thank you for calling! We'll see you at your scheduled appointment. Have a wonderful day!"
    return "Thank you for calling! Have a great day!"


# ── Order helpers ────────────────────────────────────────────────────────

def calculate_order_total(order_items: List[Dict[str, Any]]) -> float:
    """Sum price * quantity for all items."""
    return sum(i.get("price", 0) * i.get("quantity", 1) for i in order_items)


# ── Clarification detection ─────────────────────────────────────────────

_CLARIFICATION_PHRASES = [
    "i just wanted", "i didn't say", "i meant", "what i meant",
    "i already", "already ordered", "don't add", "didn't want to add",
    "no i didn't", "that's not what", "i said i wanted", "clarify",
    "i was just saying", "just clarifying", "i meant to say",
]


def detect_clarification(msg_lower: str) -> bool:
    """Return True if the message looks like a clarification, not a new order."""
    return any(phrase in msg_lower for phrase in _CLARIFICATION_PHRASES)


# ── Delivery method extraction ───────────────────────────────────────────

def extract_delivery_method(msg_lower: str, entities: Dict[str, Any]) -> Optional[str]:
    """Return 'pickup' or 'delivery' if detected, else None."""
    method = entities.get("delivery_method")
    if not method:
        if "pickup" in msg_lower or "pick up" in msg_lower or "pick it up" in msg_lower:
            method = "pickup"
        elif "delivery" in msg_lower or "deliver" in msg_lower:
            method = "delivery"
    return method


# ── Delivery address helpers ─────────────────────────────────────────────

_ADDRESS_PATTERN = re.compile(
    r'\d{1,5}\s+[\w\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|court|ct|place|pl)\b',
    re.IGNORECASE,
)


def check_delivery_address_needed(session: Dict[str, Any]) -> bool:
    """Return True if delivery is selected, no address yet, and has items."""
    return (
        session.get("delivery_method") == "delivery"
        and not session.get("delivery_address")
        and bool(session.get("order_items"))
    )


def extract_address(text: str, entities: Dict[str, Any]) -> Optional[str]:
    """Try to extract a street address from text or entities."""
    addr = entities.get("delivery_address") or entities.get("address")
    if addr:
        return addr
    m = _ADDRESS_PATTERN.search(text)
    return m.group(0).strip() if m else None


# ── Governance tier helper ───────────────────────────────────────────────

def apply_governance_tier(
    business_context: Dict[str, Any],
    reasoning_result: Dict[str, Any],
    session_id: str,
    session: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Evaluate governance tier and return structured result.

    Returns ``None`` for AUTO tier (no special handling needed).
    Otherwise returns::

        {
            "tier": <str>,
            "response": <str>,
            "events": [<event dicts>],
            "early_return": True,   # caller should stop processing
        }
    """
    from app.services.business_templates import BusinessTypeTemplate, GovernanceTier

    business_type = business_context.get("type", "general")
    detected_intent = reasoning_result.get("intent", "")
    confidence = reasoning_result.get("confidence", 0.5)
    proposed_action = reasoning_result.get("selected_action", "")
    entities = reasoning_result.get("entities", {})

    governance_tier = BusinessTypeTemplate.get_governance_tier(
        business_type=business_type,
        intent=detected_intent,
        confidence=confidence,
        action=proposed_action,
        entities=entities,
    )
    execution_policy = BusinessTypeTemplate.get_execution_policy(governance_tier)

    events: List[Dict[str, Any]] = []

    # Reasoning complete event always includes governance info
    events.append({
        "type": "reasoning_complete",
        "data": {
            "intent": detected_intent,
            "confidence": confidence,
            "selected_action": proposed_action,
            "sentiment": reasoning_result.get("sentiment"),
            "escalation_risk": reasoning_result.get("escalation_risk"),
            "governance_tier": governance_tier,
            "requires_confirmation": execution_policy.get("requires_confirmation", False),
            "requires_human_approval": execution_policy.get("requires_human_approval", False),
        },
    })

    if governance_tier == GovernanceTier.ESCALATE_IMMEDIATE:
        agent_response = reasoning_result.get("suggested_response", "Let me transfer you to someone who can better assist you.")
        if execution_policy.get("provide_safety_instructions"):
            agent_response = "I'm connecting you with our team right away. In the meantime, " + agent_response
        events.append({
            "type": "human_intervention_request",
            "reason": f"Governance tier: {governance_tier}",
            "context": {
                "intent": detected_intent,
                "confidence": confidence,
                "risk": reasoning_result.get("escalation_risk"),
                "governance_tier": governance_tier,
            },
        })
        events.append({"type": "agent_response", "text": agent_response, "reasoning": reasoning_result})
        return {"tier": governance_tier, "response": agent_response, "events": events, "early_return": True}

    if governance_tier == GovernanceTier.HUMAN_REVIEW:
        agent_response = "I need to verify this with our team. One moment please."
        events.append({
            "type": "human_approval_required",
            "action": proposed_action,
            "context": {"intent": detected_intent, "confidence": confidence, "entities": entities},
        })
        events.append({"type": "agent_response", "text": agent_response, "reasoning": reasoning_result})
        return {"tier": governance_tier, "response": agent_response, "events": events, "early_return": True}

    if governance_tier == GovernanceTier.PRIORITY_FLOW:
        safety_response = "For your safety, please follow these instructions: "
        if business_type == "hvac":
            safety_response = "If you smell gas or suspect a leak, please evacuate immediately and call 911. Then I'll connect you with our emergency technician."
        elif business_type in ("medical", "dental"):
            safety_response = "For urgent medical concerns, please call 911 or go to your nearest emergency room. I'm connecting you with our medical team now."
        elif business_type == "law_firm":
            safety_response = "This sounds time-sensitive. I'm connecting you with an attorney right away."
        agent_response = safety_response + " " + reasoning_result.get("suggested_response", "Let me help you.")
        events.append({
            "type": "human_intervention_request",
            "reason": f"Priority flow triggered for {detected_intent}",
            "context": {
                "intent": detected_intent,
                "confidence": confidence,
                "risk": reasoning_result.get("escalation_risk"),
                "governance_tier": governance_tier,
            },
        })
        events.append({"type": "agent_response", "text": agent_response, "reasoning": reasoning_result})
        return {"tier": governance_tier, "response": agent_response, "events": events, "early_return": True}

    if governance_tier == GovernanceTier.CONFIRM_BEFORE_EXECUTE:
        confirmation_prompt = f"Would you like me to proceed with {proposed_action.replace('_', ' ').lower()}? "
        agent_response = confirmation_prompt + reasoning_result.get("suggested_response", "I'm here to help.")
        if session is not None:
            session["pending_confirmation"] = {
                "action": proposed_action,
                "entities": entities,
                "governance_tier": governance_tier,
            }
        # Don't early-return — let normal action handling continue with modified response
        return {"tier": governance_tier, "response": agent_response, "events": events, "early_return": False}

    # AUTO tier — emit reasoning_complete event, no special handling
    return None
