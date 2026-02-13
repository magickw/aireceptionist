from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
import json
import base64
import asyncio
from typing import Dict
from app.services.nova_service import nova_service
from app.core.agent import agent_core

router = APIRouter()

@router.post("/incoming-call")
async def incoming_call(request: Request):
    """
    Handle incoming call webhook from Twilio.
    Returns TwiML to connect to the WebSocket stream.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    host = request.headers.get("host")
    
    # Construct the WebSocket URL
    # In production, this should use wss:// and the correct domain
    ws_url = f"wss://{host}/api/v1/twilio/ws"
    
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to the AI Receptionist.</Say>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="callSid" value="{call_sid}" />
        </Stream>
    </Connect>
</Response>
"""
    return Response(content=twiml_response, media_type="application/xml")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    stream_sid = None
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data["event"] == "connected":
                print("Twilio Media Stream Connected")
                
            elif data["event"] == "start":
                stream_sid = data["start"]["streamSid"]
                call_sid = data["start"]["callSid"]
                print(f"Stream started: {stream_sid} for call {call_sid}")
                
            elif data["event"] == "media":
                payload = data["media"]["payload"]
                chunk = base64.b64decode(payload)
                
                # TODO: STT Integration
                # 1. Buffer chunks (VAD - Voice Activity Detection)
                # 2. Send to Amazon Transcribe Streaming or Whisper
                
                # MOCK STT for Prototype:
                # We can't easily do STT here without external dependencies or heavy lifting.
                # For the sake of the 'hackathon' architecture, we assume 'text' is extracted.
                
                # Only processing occasionally to simulate turns (Real implementation needs VAD)
                pass 
                
            elif data["event"] == "stop":
                print("Stream stopped")
                break
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
