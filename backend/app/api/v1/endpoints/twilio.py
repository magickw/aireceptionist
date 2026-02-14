from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
import json
import base64
import asyncio
from typing import Dict, Optional
import os
import boto3

from app.api import deps
from app.models.models import User, Business
from app.services.nova_sonic import nova_sonic
from app.services.nova_reasoning import nova_reasoning

router = APIRouter()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


@router.post("/incoming-call")
async def incoming_call(request: Request):
    """
    Handle incoming call webhook from Twilio.
    Returns TwiML to connect to the WebSocket stream.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    from_number = form_data.get("From")
    host = request.headers.get("host")
    
    # Construct the WebSocket URL
    ws_url = f"wss://{host}/api/twilio/ws"
    
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to the AI Receptionist. Please wait.</Say>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="callSid" value="{call_sid}" />
            <Parameter name="from" value="{from_number}" />
        </Stream>
    </Connect>
</Response>
"""
    return Response(content=twiml_response, media_type="application/xml")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.
    Handles bidirectional audio streaming with Nova AI processing.
    """
    await websocket.accept()
    stream_sid = None
    call_sid = None
    from_number = None
    
    # Audio buffers
    audio_buffer = []
    conversation_history = []
    
    # Nova Sonic handler
    sonic = nova_sonic
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data["event"] == "connected":
                print("Twilio Media Stream Connected")
                # Send configuration
                await websocket.send_json({
                    "event": "configure",
                    "encoding": "audio.mulaw",
                    "sampleRate": 8000,
                    "bitsPerSample": 16,
                    "channels": 1
                })
                
            elif data["event"] == "start":
                stream_sid = data["start"]["streamSid"]
                call_sid = data["start"]["callSid"]
                from_number = data["start"].get("parameters", {}).get("from", "unknown")
                print(f"Stream started: {stream_sid} for call {call_sid} from {from_number}")
                
                # Send greeting
                greeting_audio = await sonic.process_text_to_speech(
                    "Hello! Thank you for calling. I'm the AI receptionist. How can I help you today?"
                )
                if greeting_audio:
                    # Convert to mulaw for Twilio (16kHz -> 8kHz would be needed in production)
                    greeting_b64 = base64.b64encode(greeting_audio).decode('utf-8')
                    await websocket.send_json({
                        "event": "media",
                        "media": {
                            "content": greeting_b64
                        }
                    })
                
            elif data["event"] == "media":
                payload = data["media"]["payload"]
                
                # Decode audio (Twilio sends base64-encoded mulaw)
                try:
                    audio_chunk = base64.b64decode(payload)
                    audio_buffer.append(audio_chunk)
                    
                    # Process when we have enough audio (e.g., ~1 second)
                    if len(audio_buffer) >= 8:  # 8 chunks = ~1 second of 8kHz audio
                        combined_audio = b''.join(audio_buffer)
                        audio_buffer = []  # Clear buffer for next chunk
                        
                        # Process through Nova Sonic pipeline
                        try:
                            # Get text response using Nova reasoning
                            # In production, this would use actual STT
                            # For now, we simulate with a prompt
                            
                            # Get business context for the AI
                            # (In production, fetch from database based on caller)
                            context = {
                                "business_context": {
                                    "name": "Demo Business",
                                    "hours": "9 AM to 5 PM",
                                    "services": ["consultation", "support"]
                                },
                                "customer_context": {
                                    "caller_number": from_number
                                }
                            }
                            
                            # For demo, we'll generate a response
                            # In production: real STT -> Nova reasoning -> TTS
                            response_text = "I'm here to help you. Please hold on while I process your request."
                            
                            # Synthesize speech
                            response_audio = await sonic.process_text_to_speech(response_text)
                            
                            if response_audio:
                                # Send audio back to Twilio
                                audio_b64 = base64.b64encode(response_audio).decode('utf-8')
                                await websocket.send_json({
                                    "event": "media",
                                    "media": {
                                        "content": audio_b64
                                    }
                                })
                                
                        except Exception as e:
                            print(f"Error processing audio: {e}")
                            
                except Exception as e:
                    print(f"Error decoding audio: {e}")
                    
            elif data["event"] == "stop":
                print("Stream stopped")
                
                # Save conversation to database (optional)
                # In production, store call recording and transcript
                
                # Send goodbye
                goodbye_audio = await sonic.process_text_to_speech(
                    "Thank you for calling. Have a great day!"
                )
                if goodbye_audio:
                    goodbye_b64 = base64.b64encode(goodbye_audio).decode('utf-8')
                    await websocket.send_json({
                        "event": "media",
                        "media": {
                            "content": goodbye_b64
                        }
                    })
                break
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error in websocket: {e}")


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
    message = body.get("message", "This is an automated call from your AI Receptionist.")
    
    if not to_number:
        return {"error": "to_number is required"}
    
    try:
        # Get user's business for context
        business = db.query(Business).filter(Business.user_id == current_user.id).first()
        
        # Initialize Twilio client
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Create TwiML for the call
        host = request.headers.get("host", "receptium.onrender.com")
        twiml_url = f"https://{host}/api/twilio/outbound-twiml"
        
        # Make the call
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER or "+15005550000",  # Use configured number or trial
            twiml=f"<Response><Say>{message}</Say></Response>",
            record=True
        )
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "to": to_number
        }
        
    except ImportError:
        return {"error": "Twilio library not installed"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/outbound-twiml")
async def outbound_twiml(request: Request):
    """
    TwiML for outbound calls - can connect to AI stream.
    """
    body = await request.json()
    message = body.get("message", "Hello from AI Receptionist.")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{message}</Say>
    <Record action="/api/twilio/recording-complete" maxLength="60" />
</Response>
"""
    return Response(content=twiml, media_type="application/xml")
