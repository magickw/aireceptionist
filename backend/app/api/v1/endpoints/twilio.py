"""
Twilio Voice Integration with Nova 2 Sonic
Handles real-time voice communication via Twilio Media Streams with full AI reasoning
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
import json
import base64
import asyncio
from typing import Dict, Any, Optional
import os
import boto3

from app.api import deps
from app.models.models import User, Business, CallSession
from app.services.nova_sonic import nova_sonic
from app.services.voice_helpers import mulaw_to_pcm16, pcm16_to_mulaw
from app.core.config import settings as app_settings

router = APIRouter()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


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


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    business_id: int = Query(..., description="Business ID for the AI context"),
    call_sid: str = Query(..., description="Twilio Call SID"),
    from_number: str = Query(..., description="Caller phone number"),
    db: Session = Depends(deps.get_db)
):
    """
    WebSocket endpoint for Twilio Media Streams.
    Handles bidirectional audio streaming with full Nova AI processing.
    
    This implementation matches the call simulator experience:
    - Real-time STT (Amazon Transcribe)
    - Full Nova 2 Lite reasoning engine
    - Tool execution (bookings, orders, etc.)
    - Business context from database
    - Conversation history tracking
    - Auto-stop on silence detection
    """
    await websocket.accept()
    
    # Get business context from database
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        await websocket.close(code=4000, reason="Business not found")
        return
    
    # Build business context for Nova
    business_context = {
        "name": business.name,
        "type": business.type,
        "phone": business.phone,
        "address": business.address,
        "services": business.services or [],
        "operating_hours": business.operating_hours or {},
        "menu": business.menu or [],
        "business_id": business.id,
    }
    
    # Check for custom welcome greeting to personalize AI response
    from app.services.voice_greeting_service import voice_greeting_service
    welcome_greeting = voice_greeting_service.get_active_greeting(db, business_id, "welcome")
    if welcome_greeting and welcome_greeting.get("text"):
        business_context["welcome_message"] = welcome_greeting["text"]
    
    customer_context = {
        "name": "Unknown",
        "phone": from_number,
        "call_count": 0,
        "last_contact": None,
        "satisfaction_score": 0,
        "preferred_services": [],
        "complaint_count": 0,
    }
    
    # Create Nova Sonic streaming session
    sonic_session = await nova_sonic.create_streaming_session(
        session_id=call_sid,
        business_context=business_context,
        customer_context=customer_context,
        db=db,
    )
    
    if not sonic_session:
        await websocket.close(code=4000, reason="Failed to create AI session")
        return
    
    # Audio buffers
    audio_buffer = []
    conversation_history = []
    
    # Twilio stream state
    stream_sid = None
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data["event"] == "connected":
                print(f"[Twilio WS] Connected for call {call_sid} from {from_number}")
                # Send configuration to Twilio
                await websocket.send_json({
                    "event": "configure",
                    "encoding": "audio/mulaw",
                    "sampleRate": 8000,
                    "bitsPerSample": 16,
                    "channels": 1
                })
                
            elif data["event"] == "start":
                stream_sid = data["start"]["streamSid"]
                print(f"[Twilio WS] Stream started: {stream_sid}")
                
                # Start background tasks first
                asyncio.create_task(_relay_twilio_messages(websocket, sonic_session, stream_sid))
                asyncio.create_task(_relay_twilio_tools(sonic_session, business_id, db))
                
                # Start Nova Sonic session and trigger initial greeting
                await sonic_session.start_user_turn()
                
                # Immediately end the turn to trigger AI greeting
                # This will make the AI say hello first
                await sonic_session.end_user_turn()
                
            elif data["event"] == "media":
                # Twilio sends base64-encoded mulaw audio at 8kHz
                payload = data["media"]["payload"]
                
                try:
                    # Decode base64
                    mulaw_audio = base64.b64decode(payload)
                    
                    # Convert mulaw 8kHz → PCM16 16kHz for Nova
                    pcm16_audio = mulaw_to_pcm16(mulaw_audio)
                    
                    # Stream to Nova Sonic
                    if sonic_session.is_active:
                        await sonic_session.send_audio_chunk(pcm16_audio)
                    
                except Exception as e:
                    print(f"[Twilio WS] Error processing audio: {e}")
                    
            elif data["event"] == "stop":
                print(f"[Twilio WS] Stream stopped: {stream_sid}")
                
                # End user turn
                if sonic_session.is_active:
                    await sonic_session.end_user_turn()
                
                # Close session
                await sonic_session.close()
                break
                
            elif data["event"] == "clear":
                # Twilio sends this when audio stream is cleared
                pass
                
    except WebSocketDisconnect:
        print(f"[Twilio WS] WebSocket disconnected for call {call_sid}")
    except Exception as e:
        print(f"[Twilio WS] Error: {e}")
    finally:
        # Clean up session
        if sonic_session.is_active:
            await sonic_session.close()


async def _relay_twilio_messages(
    websocket: WebSocket,
    sonic_session: Any,
    stream_sid: str,
):
    """
    Relay messages from Nova Sonic to Twilio WebSocket.
    
    Handles:
    - Text chunks (for transcription display)
    - Audio chunks (converted from PCM16 16kHz to mulaw 8kHz)
    - Thinking/reasoning events
    - Tool execution results
    """
    try:
        while sonic_session.is_active:
            item = await sonic_session.text_queue.get()
            if item is None:
                break
            
            # Handle thinking/reasoning events
            if item.get("thinking"):
                # Could log reasoning for analytics
                continue
            
            # Handle text chunks (transcription)
            if item.get("chunk"):
                # Twilio doesn't have a way to display text to the caller
                # but we could log it for analytics
                continue
            
            # Handle audio chunks
            if item.get("audio"):
                try:
                    # Decode base64 PCM16 16kHz
                    pcm16_audio = base64.b64decode(item["audio"])
                    
                    # Convert PCM16 16kHz → mulaw 8kHz for Twilio
                    mulaw_audio = pcm16_to_mulaw(pcm16_audio)
                    
                    # Encode to base64
                    mulaw_b64 = base64.b64encode(mulaw_audio).decode('utf-8')
                    
                    # Send to Twilio
                    await websocket.send_json({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {
                            "payload": mulaw_b64
                        }
                    })
                    
                except Exception as e:
                    print(f"[Twilio Relay] Error sending audio: {e}")
            
            # Handle turn complete
            if item.get("turn_complete"):
                # Could send a marker event
                pass
                
    except WebSocketDisconnect:
        print("[Twilio Relay] WebSocket disconnected")
    except Exception as e:
        print(f"[Twilio Relay] Error: {e}")


async def _relay_twilio_tools(
    sonic_session: Any,
    business_id: int,
    db: Session,
):
    """
    Relay tool execution results from Nova to Twilio.
    """
    try:
        while sonic_session.is_active:
            item = await sonic_session.tool_queue.get()
            
            tool_name = item.get("name", "")
            tool_input = item.get("input", {})
            tool_use_id = item.get("tool_use_id", "")
            
            # Execute tool (reuse voice.py tool handler)
            from app.api.v1.endpoints.voice import handle_tool_use
            
            result = await handle_tool_use(
                tool_name=tool_name,
                tool_input=tool_input,
                business_id=business_id,
                db=db,
                ws_session={},  # No WebSocket session for Twilio
                business_context=sonic_session.business_context,
                customer_context=sonic_session.customer_context,
            )
            
            # Send tool result back to Nova
            await sonic_session.send_tool_result(tool_use_id, result)
            
    except Exception as e:
        print(f"[Twilio Tools] Error: {e}")


@router.post("/outbound-call")
async def initiate_outbound_call(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Initiate an outbound call using Twilio.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"error": "Twilio not configured"}
    
    body = await request.json()
    to_number = body.get("to_number")
    business_id = body.get("business_id", 1)
    
    if not to_number:
        return {"error": "to_number is required"}
    
    try:
        # Get business
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        # Initialize Twilio client
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Create TwiML URL that connects to our WebSocket
        host = request.headers.get("host", "receptium.onrender.com")
        ws_url = f"wss://{host}/api/twilio/ws?business_id={business_id}&call_sid={{CallSid}}&from_number={to_number}"
        
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
            from_=TWILIO_PHONE_NUMBER or "+15005550000",
            twiml=twiml,
            record=True
        )
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "to": to_number,
            "from": call.from_
        }
        
    except ImportError:
        return {"error": "Twilio library not installed"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/status")
async def twilio_status():
    """
    Check Twilio configuration status.
    """
    configured = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)
    
    return {
        "configured": configured,
        "phone_number": TWILIO_PHONE_NUMBER if configured else None,
        "has_credentials": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
    }