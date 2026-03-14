"""
Twilio Voice Integration with Nova 2 Sonic
Handles real-time voice communication via Twilio Media Streams with full AI reasoning
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
import array
import json
import base64
import asyncio
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import re
import boto3

from app.api import deps
from app.models.models import User, Business, CallSession
from app.services.nova_sonic import nova_sonic
from app.services.voice_helpers import mulaw_to_pcm16, pcm16_to_mulaw
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("twilio")

router = APIRouter()

# Silence detection constants - tuned for robustness against ambient noise
SILENCE_THRESHOLD_INT16 = 1500   # RMS below this = silence (increased from 500 for noise rejection)
SILENCE_DURATION_MS = 1500       # ms of silence before end_user_turn (increased from 1200)
MIN_RECORDING_DURATION_MS = 1200 # minimum ms before silence detection engages (increased from 800)
MIN_SPEECH_DURATION_MS = 500     # minimum ms of actual speech before considering turn valid


def validate_e164_phone_number(phone: str) -> tuple[bool, str]:
    """
    Validate phone number is in E.164 format.
    Returns (is_valid, error_message).
    """
    if not phone:
        return False, "Phone number is required"
    
    # E.164 format: +[country code][number], max 15 digits
    e164_pattern = r'^\+[1-9]\d{1,14}$'
    if not re.match(e164_pattern, phone):
        return False, f"Phone number must be in E.164 format (e.g., +12345678900), got: {phone}"
    
    return True, ""


def get_base_url(request: Request = None) -> str:
    """Get the base URL for webhooks and WebSocket connections."""
    if settings.APP_BASE_URL:
        return settings.APP_BASE_URL.rstrip("/")
    if request:
        host = request.headers.get("host", "localhost")
        scheme = "https" if request.url.scheme == "https" or "x-forwarded-proto" in request.headers else "http"
        return f"{scheme}://{host}"
    return "https://receptium.onrender.com"


@router.post("/incoming-call")
async def incoming_call(request: Request, db: Session = Depends(deps.get_db)):
    """
    Handle incoming call webhook from Twilio.
    Returns TwiML to play welcome greeting (if configured) then connect to the WebSocket stream.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    from_number = form_data.get("From")
    to_number = form_data.get("To")
    host = request.headers.get("host")
    
    # Find business by phone number
    business = db.query(Business).filter(Business.phone == to_number).first()
    if not business:
        # Fallback to default business
        business = db.query(Business).filter(Business.id == 1).first()
    
    business_id = business.id if business else 1
    
    # Check for active welcome greeting
    from app.services.voice_greeting_service import voice_greeting_service
    welcome_greeting = voice_greeting_service.get_active_greeting(db, business_id, "welcome")
    
    # Construct the WebSocket URL with business context
    ws_url = f"wss://{host}/api/twilio/ws?business_id={business_id}&call_sid={call_sid}&from_number={from_number}"
    
    # Build TwiML
    twiml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<Response>']
    
    # If there's a welcome greeting, play it
    if welcome_greeting:
        greeting_text = welcome_greeting.get("text", "")
        if greeting_text:
            twiml_parts.append(f'    <Say>{greeting_text}</Say>')
    
    # Connect to WebSocket stream
    twiml_parts.append('    <Connect>')
    twiml_parts.append(f'        <Stream url="{ws_url}">')
    twiml_parts.append(f'            <Parameter name="callSid" value="{call_sid}" />')
    twiml_parts.append(f'            <Parameter name="from" value="{from_number}" />')
    twiml_parts.append('        </Stream>')
    twiml_parts.append('    </Connect>')
    twiml_parts.append('</Response>')
    
    twiml_response = '\n'.join(twiml_parts)
    return Response(content=twiml_response, media_type="application/xml")


def _rms_amplitude(pcm16_bytes: bytes) -> float:
    """Compute RMS amplitude of PCM16 audio on the int16 scale (0-32768)."""
    if len(pcm16_bytes) < 2:
        return 0.0
    samples = array.array('h')
    samples.frombytes(pcm16_bytes)
    if not samples:
        return 0.0
    sum_sq = sum(s * s for s in samples)
    return math.sqrt(sum_sq / len(samples))


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    business_id: int = Query(..., description="Business ID for the AI context"),
    call_sid: Optional[str] = Query(None, description="Twilio Call SID"),
    from_number: Optional[str] = Query(None, description="Caller phone number"),
    campaign_id: Optional[int] = Query(None, description="Campaign ID for outbound calls"),
    campaign_call_id: Optional[int] = Query(None, description="Campaign call ID"),
    briefing: Optional[str] = Query(None, description="Campaign briefing text"),
    db: Session = Depends(deps.get_db)
):
    """
    WebSocket endpoint for Twilio Media Streams.
    Handles bidirectional audio streaming with full Nova AI processing.
    """
    await websocket.accept()

    # Get business context from database
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        await websocket.close(code=4000, reason="Business not found")
        return

    # Twilio stream state
    stream_sid = None
    relay_task = None
    sonic_session = None
    ws_session = None
    conversation_history = []

    # Silence detection state
    _in_user_turn = False
    _silence_start = None   # loop-time when silence began
    _turn_start = None      # loop-time when current turn began
    _speech_frames = 0      # count of non-silent frames in current turn
    _speech_duration_ms = 0 # accumulated speech duration in current turn

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data["event"] == "connected":
                print(f"[Twilio WS] Connected event received")

            elif data["event"] == "start":
                stream_sid = data["start"]["streamSid"]
                
                # If call_sid/from_number were not in query, get them from the start event
                if not call_sid:
                    call_sid = data["start"].get("callSid")
                if not from_number:
                    # Twilio sends from in start.customParameters if we added it, 
                    # otherwise we might not have it here unless we pass it.
                    # Fallback to a placeholder if absolutely missing.
                    from_number = data["start"].get("customParameters", {}).get("from") or from_number or "Unknown"

                print(f"[Twilio WS] Stream started: {stream_sid} (CallSid: {call_sid})")

                # 1. Build business context for Nova
                business_context = {
                    "name": business.name,
                    "type": business.type,
                    "phone": business.phone,
                    "address": business.address,
                    "services": business.services or [],
                    "operating_hours": business.operating_hours or {},
                    "menu": business.menu or [],
                    "business_id": business.id,
                    "language": business.settings.get("language", "en-US") if business.settings else "en-US"
                }

                # Personalize AI response with greeting
                from app.services.voice_greeting_service import voice_greeting_service
                welcome_greeting = voice_greeting_service.get_active_greeting(db, business_id, "welcome")
                if welcome_greeting and welcome_greeting.get("text"):
                    business_context["welcome_message"] = welcome_greeting["text"]

                # E5: Inject campaign briefing for outbound calls
                if briefing:
                    import urllib.parse
                    campaign_briefing = urllib.parse.unquote(briefing)
                    business_context["welcome_message"] = campaign_briefing

                customer_context = {
                    "name": "Unknown",
                    "phone": from_number,
                    "call_count": 0,
                    "last_contact": None,
                    "satisfaction_score": 0,
                    "preferred_services": [],
                    "complaint_count": 0,
                }

                # 2. Create Nova Sonic streaming session
                sonic_session = await nova_sonic.create_streaming_session(
                    session_id=call_sid,
                    business_context=business_context,
                    customer_context=customer_context,
                    db=db,
                    language=business_context.get("language", "en-US")
                )

                if not sonic_session:
                    await websocket.close(code=4000, reason="Failed to create AI session")
                    return

                # E2: Register session and publish call_start event
                try:
                    from app.services.event_bus import event_bus, session_registry
                    session_registry.register(call_sid, {
                        "business_id": business_id,
                        "customer_phone": from_number,
                        "sonic_session": sonic_session,
                        "source": "twilio",
                        "campaign_id": campaign_id,
                    })
                    import asyncio as _aio
                    _aio.get_event_loop().create_task(event_bus.publish({
                        "type": "call_start",
                        "session_id": call_sid,
                        "business_id": business_id,
                        "customer_phone": from_number,
                        "source": "twilio",
                        "campaign_id": campaign_id,
                    }))
                except Exception:
                    pass

                # Session dict for tool execution
                ws_session = {
                    "order_items": [],
                    "created_at": datetime.now(timezone.utc),
                    "business_id": business_id,
                    "customer_name": None,
                    "customer_phone": from_number,
                    "_session_id": call_sid,
                }

                # 3. Launch 4-queue relay as background task
                relay_task = asyncio.create_task(
                    _run_twilio_relay(
                        sonic_session=sonic_session,
                        websocket=websocket,
                        stream_sid=stream_sid,
                        ws_session=ws_session,
                        business_id=business_id,
                        business_context=business_context,
                        conversation_history=conversation_history,
                        db=db,
                    )
                )

                # Trigger AI greeting via text message
                await sonic_session.send_text_message("Please greet the caller.")
                print(f"[Twilio WS] AI greeting triggered")

            elif data["event"] == "media":
                if not sonic_session or not sonic_session.is_active:
                    continue

                payload = data["media"]["payload"]
                try:
                    mulaw_audio = base64.b64decode(payload)
                    pcm16_audio = mulaw_to_pcm16(mulaw_audio)
                    rms = _rms_amplitude(pcm16_audio)
                    now = asyncio.get_event_loop().time()

                    # Each media chunk is ~20ms at 8kHz mulaw (160 samples)
                    FRAME_DURATION_MS = 20

                    if rms >= SILENCE_THRESHOLD_INT16:
                        # Non-silent frame (speech detected)
                        _silence_start = None
                        _speech_frames += 1
                        _speech_duration_ms += FRAME_DURATION_MS

                        if not _in_user_turn:
                            # User started speaking — begin new turn + barge-in
                            _in_user_turn = True
                            _turn_start = now
                            _speech_frames = 1
                            _speech_duration_ms = FRAME_DURATION_MS
                            await sonic_session.start_user_turn()

                            # Barge-in: clear any in-flight TTS audio
                            try:
                                await websocket.send_json({
                                    "event": "clear",
                                    "streamSid": stream_sid,
                                })
                            except Exception:
                                pass
                            print(f"[Twilio WS] User turn started (barge-in, rms={rms:.0f})")

                        await sonic_session.send_audio_chunk(pcm16_audio)

                    else:
                        # Silent frame
                        if _in_user_turn:
                            await sonic_session.send_audio_chunk(pcm16_audio)

                            if _silence_start is None:
                                _silence_start = now

                            elapsed_silence = (now - _silence_start) * 1000  # ms
                            elapsed_turn = (now - _turn_start) * 1000 if _turn_start else 0

                            # Only end turn if we have enough speech AND enough silence
                            if (elapsed_silence >= SILENCE_DURATION_MS
                                    and elapsed_turn >= MIN_RECORDING_DURATION_MS
                                    and _speech_duration_ms >= MIN_SPEECH_DURATION_MS):
                                # Enough silence after enough speech — end the turn
                                _in_user_turn = False
                                _silence_start = None
                                _turn_start = None
                                print(f"[Twilio WS] User turn ended (silence detected, speech={_speech_duration_ms}ms, turn={elapsed_turn:.0f}ms)")
                                _speech_frames = 0
                                _speech_duration_ms = 0
                                await sonic_session.end_user_turn()

                except Exception as e:
                    print(f"[Twilio WS] Error processing audio: {e}")

            elif data["event"] == "stop":
                print(f"[Twilio WS] Stream stopped: {stream_sid}")

                # Flush remaining turn if active
                if _in_user_turn and sonic_session and sonic_session.is_active:
                    _in_user_turn = False
                    await sonic_session.end_user_turn()

                if sonic_session and sonic_session.is_active:
                    await sonic_session.close()
                break

            elif data["event"] == "clear":
                pass

    except WebSocketDisconnect:
        print(f"[Twilio WS] WebSocket disconnected for call {call_sid}")
    except Exception as e:
        print(f"[Twilio WS] Error: {e}")
    finally:
        if sonic_session and sonic_session.is_active:
            await sonic_session.close()
        if relay_task and not relay_task.done():
            relay_task.cancel()


async def _run_twilio_relay(
    sonic_session,
    websocket: WebSocket,
    stream_sid: str,
    ws_session: Dict[str, Any],
    business_id: int,
    business_context: Dict[str, Any],
    conversation_history: list,
    db: Session,
):
    """
    Background task that reads from NovaSonicStreamSession queues
    and relays events to the Twilio WebSocket.
    Mirrors _run_streaming_relay in voice.py with 4 concurrent coroutines.
    """
    from app.services.translation_service import translation_service
    from app.models.models import ConversationMessage

    def _save_message(content: str, sender: str, msg_type: str = "text"):
        """Save a conversation message to the database."""
        try:
            # English translation for non-English calls
            entities = {}
            if business_context.get("language") != "en-US":
                translated = translation_service.translate_transcript(
                    content, source_lang=business_context.get("language", "auto")
                )
                entities["translation"] = translated

            msg = ConversationMessage(
                call_session_id=ws_session.get("_session_id"),
                sender=sender,
                content=content,
                message_type=msg_type,
                entities=entities
            )
            db.add(msg)
            db.commit()
        except Exception as e:
            print(f"[Twilio Relay] Failed to save message: {e}")

    async def _relay_transcripts():
        while sonic_session.is_active:
            item = await sonic_session.transcript_queue.get()
            if item is None:
                break
            text = item.get("text", "")
            is_partial = item.get("is_partial", False)
            if not is_partial and text:
                conversation_history.append({"role": "customer", "content": text})
                _save_message(text, "customer")
                print(f"[Twilio Relay] Transcript: {text}")

    async def _relay_audio():
        while sonic_session.is_active:
            item = await sonic_session.audio_queue.get()
            if item is None:
                break
            try:
                pcm16_audio = base64.b64decode(item.get("audio", ""))
                mulaw_audio = pcm16_to_mulaw(pcm16_audio)
                mulaw_b64 = base64.b64encode(mulaw_audio).decode('utf-8')
                await websocket.send_json({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": mulaw_b64},
                })
            except Exception as e:
                print(f"[Twilio Relay] Error sending audio: {e}")
                break

    async def _relay_text():
        accumulated_text = ""
        while sonic_session.is_active:
            item = await sonic_session.text_queue.get()
            if item is None:
                if accumulated_text:
                    conversation_history.append({"role": "ai", "content": accumulated_text})
                    _save_message(accumulated_text, "ai")
                break
            if item.get("thinking"):
                continue
            if item.get("turn_complete"):
                if accumulated_text:
                    conversation_history.append({"role": "ai", "content": accumulated_text})
                    _save_message(accumulated_text, "ai")
                    print(f"[Twilio Relay] AI response: {accumulated_text[:100]}...")
                accumulated_text = ""
                continue
            chunk = item.get("chunk", "")
            accumulated_text += chunk

    async def _relay_tools():
        from app.api.v1.endpoints.voice import handle_tool_use
        while sonic_session.is_active:
            item = await sonic_session.tool_queue.get()
            if item is None:
                break
            tool_name = item.get("name", "")
            tool_input = item.get("input", {})
            tool_use_id = item.get("tool_use_id", "")

            # Log tool execution as a system message
            _save_message(f"AI using tool: {tool_name} with input {json.dumps(tool_input)}", "ai", "action")

            try:
                result = await handle_tool_use(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    ws_session=ws_session,
                    business_id=business_id,
                    business_context=business_context,
                    db=db,
                )
            except Exception as e:
                print(f"[Twilio Relay] Tool error for {tool_name}: {e}")
                result = {"success": False, "message": f"Tool execution failed: {str(e)}"}
            await sonic_session.send_tool_result(tool_use_id, result)

    await asyncio.gather(
        _relay_transcripts(),
        _relay_audio(),
        _relay_text(),
        _relay_tools(),
        return_exceptions=True,
    )
    print("[Twilio Relay] All relays stopped")


@router.post("/outbound-call")
async def initiate_outbound_call(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Initiate an outbound call using Twilio.
    """
    # Validate Twilio configuration
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {"error": "Twilio not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables."}
    
    if not settings.TWILIO_PHONE_NUMBER:
        return {"error": "Twilio phone number not configured. Set TWILIO_PHONE_NUMBER environment variable."}
    
    body = await request.json()
    to_number = body.get("to_number")
    business_id = body.get("business_id", 1)
    
    if not to_number:
        return {"error": "to_number is required"}
    
    # Validate phone number format
    is_valid, error_msg = validate_e164_phone_number(to_number)
    if not is_valid:
        return {"error": error_msg}
    
    try:
        # Get business
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        # Initialize Twilio client
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Create TwiML URL that connects to our WebSocket
        base_url = get_base_url(request)
        ws_url = f"{base_url.replace('https://', 'wss://').replace('http://', 'ws://')}/api/twilio/ws?business_id={business_id}&call_sid={{CallSid}}&from_number={to_number}"
        
        # Make the call with TwiML that connects to WebSocket
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>
"""
        
        call = client.calls.create(
            to=to_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            twiml=twiml,
            record=True
        )
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "to": to_number,
            "from": settings.TWILIO_PHONE_NUMBER
        }
        
    except ImportError:
        return {"error": "Twilio library not installed. Run: pip install twilio"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/status")
async def twilio_status():
    """
    Check Twilio configuration status.
    """
    configured = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER)
    
    return {
        "configured": configured,
        "phone_number": settings.TWILIO_PHONE_NUMBER if configured else None,
        "has_credentials": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
    }


# ======================================================================
# E5: Outbound campaign status callback
# ======================================================================

@router.post("/outbound-status")
async def outbound_status_callback(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """
    Twilio status callback for outbound campaign calls.
    Updates CampaignCall records with final call status and duration.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")  # completed, busy, no-answer, failed, canceled
    call_duration = form_data.get("CallDuration")  # seconds

    if not call_sid:
        return {"status": "ignored", "reason": "no CallSid"}

    from app.models.models import CampaignCall

    campaign_call = db.query(CampaignCall).filter(
        CampaignCall.call_session_id == call_sid
    ).first()

    if not campaign_call:
        return {"status": "ignored", "reason": "no matching campaign call"}

    # Map Twilio status to our status
    status_map = {
        "completed": "completed",
        "busy": "no_answer",
        "no-answer": "no_answer",
        "failed": "failed",
        "canceled": "failed",
    }
    campaign_call.status = status_map.get(call_status, "failed")
    if call_duration:
        campaign_call.call_duration_seconds = int(call_duration)
    campaign_call.completed_at = datetime.now(timezone.utc)

    # Update campaign metrics
    from app.models.models import Campaign
    campaign = db.query(Campaign).filter(Campaign.id == campaign_call.campaign_id).first()
    if campaign:
        if campaign_call.status == "completed":
            campaign.calls_answered = (campaign.calls_answered or 0) + 1
        campaign.calls_made = (campaign.calls_made or 0) + 1

    db.commit()
    return {"status": "updated", "campaign_call_id": campaign_call.id}


# ======================================================================
# Incoming SMS Webhook
# ======================================================================

@router.post("/sms-webhook")
async def incoming_sms_webhook(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """
    Handle incoming SMS messages from Twilio.
    
    Twilio sends form data with:
    - MessageSid: Unique identifier for the message
    - From: Phone number of the sender (E.164 format)
    - To: Phone number that received the message (E.164 format)
    - Body: The text content of the message
    - NumMedia: Number of media attachments (for MMS)
    
    Returns TwiML response (optional auto-reply).
    """
    form_data = await request.form()
    
    message_sid = form_data.get("MessageSid")
    from_number = form_data.get("From")
    to_number = form_data.get("To")
    body = form_data.get("Body", "")
    num_media = int(form_data.get("NumMedia", 0))
    
    logger.info(f"[Twilio SMS] Received SMS from {from_number} to {to_number}: {body[:100]}...")
    
    # Find business by destination phone number
    business = db.query(Business).filter(Business.phone == to_number).first()
    
    if not business:
        logger.warning(f"[Twilio SMS] No business found for phone number: {to_number}")
        # Still return empty TwiML to acknowledge receipt
        return PlainTextResponse(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
    
    # Find or create customer by phone number
    from app.models.models import Customer
    customer = db.query(Customer).filter(
        Customer.business_id == business.id,
        Customer.phone == from_number
    ).first()
    
    if not customer:
        # Create new customer
        customer = Customer(
            business_id=business.id,
            phone=from_number,
            name=f"SMS Contact ({from_number})",
        )
        db.add(customer)
        db.flush()
        logger.info(f"[Twilio SMS] Created new customer: {customer.id}")
    
    # Store the incoming message
    from app.models.models import SMSMessage
    sms_message = SMSMessage(
        business_id=business.id,
        customer_id=customer.id,
        direction="inbound",
        from_number=from_number,
        to_number=to_number,
        body=body,
        twilio_sid=message_sid,
        status="received",
    )
    db.add(sms_message)
    db.commit()
    
    logger.info(f"[Twilio SMS] Stored inbound SMS {message_sid} from customer {customer.id}")
    
    # Check if auto-reply is enabled for this business
    auto_reply = getattr(business, 'sms_auto_reply', None)
    if auto_reply and auto_reply.get('enabled'):
        reply_message = auto_reply.get('message', "Thanks for your message! We'll get back to you soon.")
        twiml_response = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply_message}</Message></Response>'
        return PlainTextResponse(content=twiml_response, media_type="application/xml")
    
    # Return empty TwiML (no auto-reply)
    return PlainTextResponse(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml"
    )


@router.post("/sms-status")
async def sms_status_callback(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """
    Handle SMS delivery status callbacks from Twilio.
    
    Twilio sends form data with:
    - MessageSid: Unique identifier for the message
    - MessageStatus: queued, sent, delivered, undelivered, failed
    - ErrorCode: Error code if failed
    - ErrorMessage: Error description if failed
    """
    form_data = await request.form()
    
    message_sid = form_data.get("MessageSid")
    message_status = form_data.get("MessageStatus")
    error_code = form_data.get("ErrorCode")
    error_message = form_data.get("ErrorMessage")
    
    logger.info(f"[Twilio SMS] Status callback: {message_sid} -> {message_status}")
    
    if error_code:
        logger.warning(f"[Twilio SMS] Error {error_code}: {error_message}")
    
    # Update SMS message status if we have it stored
    from app.models.models import SMSMessage
    sms_message = db.query(SMSMessage).filter(
        SMSMessage.twilio_sid == message_sid
    ).first()
    
    if sms_message:
        sms_message.status = message_status
        if error_code:
            sms_message.error_code = error_code
            sms_message.error_message = error_message
        db.commit()
        return {"status": "updated", "message_sid": message_sid}
    
    return {"status": "not_found", "message_sid": message_sid}