"""
Voice WebSocket Endpoint
Handles real-time voice communication with Nova 2 Sonic and reasoning
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any, AsyncGenerator
import json
import asyncio
import base64
from datetime import datetime
from app.services.nova_reasoning import nova_reasoning
from app.services.nova_sonic import nova_sonic, AudioBuffer, LatencyTracker
from app.api.deps import get_current_business_id, get_current_active_user, get_db
from app.models.models import User, Appointment
from sqlalchemy.orm import Session

router = APIRouter()


class VoiceConnectionManager:
    """Manages active WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.latency_trackers: Dict[str, LatencyTracker] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.audio_buffers[session_id] = AudioBuffer()
        self.latency_trackers[session_id] = LatencyTracker()
    
    def disconnect(self, session_id: str):
        """Remove a connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        if session_id in self.latency_trackers:
            del self.latency_trackers[session_id]
    
    async def send_json(self, session_id: str, data: Dict[str, Any]):
        """Send JSON message to a specific connection"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)
    
    async def send_bytes(self, session_id: str, data: bytes):
        """Send binary data to a specific connection"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_bytes(data)


manager = VoiceConnectionManager()


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    business_id: int = Depends(get_current_business_id)
):
    """
    WebSocket endpoint for real-time voice communication.
    
    Expected message format from client:
    {
        "type": "user_input" | "audio" | "ping" | "audio_config",
        "content": "text or base64 audio",
        "session_id": "unique_session_id",
        "context": {
            "customer_phone": "...",
            "customer_name": "...",
            "call_count": 0,
            "satisfaction_score": 4.5,
            "preferred_services": [],
            "complaint_count": 0
        }
    }
    
    Response format:
    {
        "type": "thought" | "agent_response" | "audio" | "audio_config" | "error",
        "content": "...",
        "data": {...}
    }
    """
    session_id = f"session_{business_id}_{asyncio.get_event_loop().time()}"
    
    try:
        await manager.connect(websocket, session_id)
        
        # Send connection acknowledgment with audio config
        await manager.send_json(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "Voice connection established with Nova 2 Sonic",
            "audio_config": nova_sonic.get_audio_config()
        })
        
        # Store conversation history for context
        conversation_history = []
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            content = data.get("content", "")
            context = data.get("context", {})
            
            if message_type == "ping":
                # Heartbeat - keep connection alive
                await manager.send_json(session_id, {
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            elif message_type == "user_input":
                # Process text input (for call simulator)
                conversation_history.append({
                    "role": "customer",
                    "content": content
                })
                
                # Get business context
                business_context = await _get_business_context(business_id)
                
                # Build customer context
                customer_context = {
                    "name": context.get("customer_name", "Unknown"),
                    "phone": context.get("customer_phone", "Unknown"),
                    "call_count": context.get("call_count", 0),
                    "last_contact": context.get("last_contact", "Never"),
                    "satisfaction_score": context.get("satisfaction_score", 0),
                    "preferred_services": context.get("preferred_services", []),
                    "complaint_count": context.get("complaint_count", 0)
                }
                
                # Send reasoning thoughts to UI
                await manager.send_json(session_id, {
                    "type": "thought",
                    "step": "processing",
                    "message": "Analyzing conversation with Nova 2 Lite..."
                })
                
                # Get reasoning from Nova Lite
                reasoning_result = await nova_reasoning.reason(
                    conversation=_format_conversation(conversation_history),
                    business_context=business_context,
                    customer_context=customer_context
                )
                
                # Send reasoning chain to UI for visualization
                await manager.send_json(session_id, {
                    "type": "reasoning_chain",
                    "data": reasoning_result.get("reasoning_chain", [])
                })
                
                # Send final reasoning result
                await manager.send_json(session_id, {
                    "type": "reasoning_complete",
                    "data": {
                        "intent": reasoning_result.get("intent"),
                        "confidence": reasoning_result.get("confidence"),
                        "selected_action": reasoning_result.get("selected_action"),
                        "sentiment": reasoning_result.get("sentiment"),
                        "escalation_risk": reasoning_result.get("escalation_risk")
                    }
                })
                
                # Send agent response - streaming text chunks
                agent_response = reasoning_result.get("suggested_response", "I'm here to help you.")
                
                # Stream the response in chunks
                chunk_size = 20  # characters per chunk
                for i in range(0, len(agent_response), chunk_size):
                    chunk = agent_response[i:i + chunk_size]
                    is_last = i + chunk_size >= len(agent_response)
                    
                    await manager.send_json(session_id, {
                        "type": "text_chunk",
                        "chunk": chunk,
                        "is_last": is_last,
                        "full_text": agent_response if is_last else None  # Send full text on last chunk
                    })
                    
                    # Small delay to create streaming effect
                    if not is_last:
                        await asyncio.sleep(0.02)  # 20ms delay between chunks
                
                conversation_history.append({
                    "role": "ai",
                    "content": agent_response
                })
                
                # Skip sending duplicate agent_response - text_chunk already handles it
                # (keeping for potential backwards compatibility if needed)
                # await manager.send_json(session_id, {
                #     "type": "agent_response",
                #     "text": agent_response,
                #     "reasoning": reasoning_result
                # })
                
                # Generate audio with Nova 2 Sonic (text-to-speech)
                audio_data = await nova_sonic.process_text_to_speech(agent_response)
                
                if audio_data:
                    # Send audio as base64 for WebSocket transmission
                    audio_base64 = nova_sonic.encode_audio_base64(audio_data)
                    await manager.send_json(session_id, {
                        "type": "audio",
                        "audio": audio_base64,
                        "format": "pcm16",
                        "sample_rate": 16000
                    })
                
            elif message_type == "audio":
                # Process audio input (speech-to-speech with Nova Sonic)
                try:
                    # Start latency tracking
                    tracker = manager.latency_trackers.get(session_id)
                    if tracker:
                        tracker.start()
                    
                    # Decode base64 audio
                    audio_data = nova_sonic.decode_audio_base64(content)
                    
                    # Process audio stream
                    async for response in nova_sonic.process_audio_stream(
                        _generate_audio_chunks([audio_data]),
                        {
                            "business_context": await _get_business_context(business_id),
                            "customer_context": context
                        }
                    ):
                        if response["type"] == "transcript":
                            # Customer transcript
                            conversation_history.append({
                                "role": "customer",
                                "content": response["text"]
                            })
                            
                            await manager.send_json(session_id, {
                                "type": "transcript",
                                "text": response["text"]
                            })
                        
                        elif response["type"] == "text_response":
                            # AI text response
                            conversation_history.append({
                                "role": "ai",
                                "content": response["text"]
                            })
                            
                            await manager.send_json(session_id, {
                                "type": "agent_response",
                                "text": response["text"]
                            })
                        
                        elif response["type"] == "audio":
                            # AI audio response
                            audio_base64 = nova_sonic.encode_audio_base64(response["data"])
                            await manager.send_json(session_id, {
                                "type": "audio",
                                "audio": audio_base64,
                                "format": "pcm16",
                                "sample_rate": 16000
                            })
                        
                        elif response["type"] == "complete":
                            # Processing complete
                            if tracker:
                                tracker.end()
                                metrics = tracker.get_metrics()
                                await manager.send_json(session_id, {
                                    "type": "latency_metrics",
                                    "metrics": metrics
                                })
                        
                        elif response["type"] == "error":
                            await manager.send_json(session_id, {
                                "type": "error",
                                "message": response["message"]
                            })
                
                except Exception as e:
                    await manager.send_json(session_id, {
                        "type": "error",
                        "message": f"Audio processing error: {str(e)}"
                    })
            
            elif message_type == "audio_config":
                # Send audio configuration
                await manager.send_json(session_id, {
                    "type": "audio_config",
                    "config": nova_sonic.get_audio_config()
                })
            
            elif message_type == "end_call":
                # End the call
                await manager.send_json(session_id, {
                    "type": "call_ended",
                    "message": "Call ended"
                })
                break
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await manager.send_json(session_id, {
            "type": "error",
            "message": f"Error: {str(e)}"
        })
        manager.disconnect(session_id)


async def _get_business_context(business_id: int, db: Session = None) -> Dict[str, Any]:
    """
    Get business context from database.
    """
    # If no db session provided, try to get one
    if db is None:
        try:
            from app.api.deps import get_db
            gen = get_db()
            db = next(gen)
        except:
            # Fallback if db not available
            return {
                "name": "Demo Business",
                "type": "general",
                "services": ["Consultation"],
                "operating_hours": "Mon-Fri 9AM-5PM",
                "available_slots": ["Today 2PM", "Tomorrow 10AM"]
            }
    
    from app.models.models import Business, MenuItem
    
    business = db.query(Business).filter(Business.id == business_id).first()
    
    if not business:
        # Fallback to default if business not found
        return {
            "name": "Demo Business",
            "type": "general",
            "services": ["Consultation"],
            "operating_hours": "Mon-Fri 9AM-5PM",
            "available_slots": ["Today 2PM", "Tomorrow 10AM"],
            "menu": []
        }
    
    # Get services from business settings if available
    services = business.settings.get("services", []) if business.settings else []
    if not services:
        services = ["Consultation", "Service 1", "Service 2"]
    
    # Get menu items if available
    menu_items = db.query(MenuItem).filter(
        MenuItem.business_id == business_id,
        MenuItem.is_active == True,
        MenuItem.available == True
    ).all()
    
    menu = []
    if menu_items:
        menu = [
            {
                "name": item.name,
                "description": item.description,
                "price": float(item.price) if item.price else None,
                "category": item.category,
                "dietary_info": item.dietary_info
            }
            for item in menu_items
        ]
    
    return {
        "name": business.name,
        "type": business.type or "general",
        "services": services,
        "operating_hours": business.settings.get("operating_hours", "Mon-Fri 9AM-5PM") if business.settings else "Mon-Fri 9AM-5PM",
        "available_slots": business.settings.get("available_slots", ["Today 2PM", "Tomorrow 10AM"]) if business.settings else ["Today 2PM", "Tomorrow 10AM"],
        "menu": menu
    }


def _format_conversation(history: list) -> str:
    """Format conversation history for Nova reasoning"""
    formatted = []
    for msg in history:
        role = "Customer" if msg["role"] == "customer" else "AI Assistant"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)


async def _generate_audio_chunks(audio_data: list[bytes]) -> AsyncGenerator[bytes, None]:
    """Generate audio chunks from audio data list"""
    for chunk in audio_data:
        yield chunk


@router.post("/test-reasoning")
async def test_reasoning(
    message: str,
    business_id: int = Depends(get_current_business_id)
):
    """
    Test endpoint for Nova reasoning without WebSocket.
    Useful for debugging and testing.
    """
    business_context = await _get_business_context(business_id)
    customer_context = {
        "name": "Test Customer",
        "phone": "+1 (555) 123-4567",
        "call_count": 0,
        "last_contact": "Never",
        "satisfaction_score": 0,
        "preferred_services": [],
        "complaint_count": 0
    }
    
    result = await nova_reasoning.reason(
        conversation=f"Customer: {message}",
        business_context=business_context,
        customer_context=customer_context
    )
    
    return result


@router.post("/test-audio")
async def test_audio(
    text: str,
    business_id: int = Depends(get_current_business_id)
):
    """
    Test endpoint for Nova Sonic text-to-speech.
    Returns audio data in base64 format.
    """
    try:
        audio_data = await nova_sonic.process_text_to_speech(text)
        
        if audio_data:
            audio_base64 = nova_sonic.encode_audio_base64(audio_data)
            return {
                "success": True,
                "audio": audio_base64,
                "format": "pcm16",
                "sample_rate": 16000,
                "text": text
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate audio"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/audio-config")
async def get_audio_config(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get audio configuration for the client.
    """
    return {
        "config": nova_sonic.get_audio_config(),
        "model": "Nova 2 Sonic"
    }


# HTTP Fallback endpoints for Vercel (no WebSocket support)
from pydantic import BaseModel
from datetime import datetime

class HTTPSessionStore:
    """Simple in-memory session store for HTTP fallback"""
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, session_id: str, business_id: int, customer_phone: str = "", call_type: str = "simulator"):
        self.sessions[session_id] = {
            "business_id": business_id,
            "customer_phone": customer_phone,
            "call_type": call_type,
            "conversation_history": [],
            "events": [],
            "created_at": datetime.utcnow(),
            "active": True
        }
        return self.sessions[session_id]
    
    def get_session(self, session_id: str):
        return self.sessions.get(session_id)
    
    def add_event(self, session_id: str, event: dict):
        if session_id in self.sessions:
            self.sessions[session_id]["events"].append(event)
    
    def end_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["active"] = False
    
    def get_and_clear_events(self, session_id: str):
        if session_id in self.sessions:
            events = self.sessions[session_id]["events"].copy()
            self.sessions[session_id]["events"] = []
            return events
        return []

session_store = HTTPSessionStore()


class SessionCreate(BaseModel):
    customer_phone: str = "+15551234567"
    call_type: str = "simulator"


class MessageInput(BaseModel):
    text: str


@router.post("/session")
async def create_session(
    session_data: SessionCreate,
    business_id: int = Depends(get_current_business_id)
):
    """Create a new HTTP session for call simulator"""
    import uuid
    session_id = f"http_{business_id}_{uuid.uuid4().hex[:8]}"
    session_store.create_session(session_id, business_id, session_data.customer_phone, session_data.call_type)
    return {"session_id": session_id, "status": "active"}


@router.get("/session/{session_id}/events")
async def get_session_events(session_id: str):
    """Poll for events (HTTP fallback for WebSocket)"""
    session = session_store.get_session(session_id)
    if not session:
        return {"events": [], "status": "not_found"}
    
    events = session_store.get_and_clear_events(session_id)
    return {
        "events": events,
        "status": "active" if session["active"] else "ended"
    }


@router.post("/session/{session_id}/message")
async def send_http_message(
    session_id: str,
    message: MessageInput,
    db: Session = Depends(get_db)
):
    """Send a message via HTTP (HTTP fallback)"""
    print(f"[Voice API] send_http_message called - session: {session_id}, text: {message.text[:50]}...")
    
    session = session_store.get_session(session_id)
    if not session:
        return {"error": "Session not found", "status": 404}
    
    business_id = session["business_id"]
    customer_phone = session.get("customer_phone", "+1555000000")
    customer_name = "Customer"
    
    # Add to conversation history
    session["conversation_history"].append({
        "role": "customer",
        "content": message.text
    })
    
    # Add thought event
    session_store.add_event(session_id, {
        "type": "thought",
        "step": "processing",
        "message": "Analyzing conversation with Nova 2 Lite..."
    })
    
    # Get business context
    business_context = await _get_business_context(business_id)
    
    # Build customer context
    customer_context = {
        "name": "Customer",
        "phone": session.get("customer_phone", "Unknown"),
        "call_count": 0,
        "last_contact": "Never",
        "satisfaction_score": 0,
        "preferred_services": [],
        "complaint_count": 0
    }
    
    # Get reasoning from Nova Lite
    reasoning_result = await nova_reasoning.reason(
        conversation=_format_conversation(session["conversation_history"]),
        business_context=business_context,
        customer_context=customer_context
    )
    
    # Add reasoning chain event
    session_store.add_event(session_id, {
        "type": "reasoning_chain",
        "data": reasoning_result.get("reasoning_chain", [])
    })
    
    # Add reasoning complete event
    session_store.add_event(session_id, {
        "type": "reasoning_complete",
        "data": {
            "intent": reasoning_result.get("intent"),
            "confidence": reasoning_result.get("confidence"),
            "selected_action": reasoning_result.get("selected_action"),
            "sentiment": reasoning_result.get("sentiment"),
            "escalation_risk": reasoning_result.get("escalation_risk")
        }
    })
    
    # Get agent response
    agent_response = reasoning_result.get("suggested_response", "I'm here to help you.")
    
    # Add only agent_response event (frontend handles single message display)
    # Do NOT add text_chunk to avoid duplicates
    session_store.add_event(session_id, {
        "type": "agent_response",
        "text": agent_response,
        "reasoning": reasoning_result
    })
    
    # Create appointment if action is CREATE_APPOINTMENT or if AI confirms scheduling
    selected_action = reasoning_result.get("selected_action", "")
    entities = reasoning_result.get("entities", {})
    
    # Use extracted phone from entities if available, otherwise use session phone
    extracted_phone = entities.get("customer_phone")
    if extracted_phone:
        customer_phone = extracted_phone
    
    # Also try to get customer name from entities
    extracted_name = entities.get("customer_name")
    if extracted_name:
        customer_name = extracted_name
    
    # Also check if the AI response mentions scheduling an appointment
    appointment_created = False
    
    if selected_action == "CREATE_APPOINTMENT":
        date_str = entities.get("date")
        time_str = entities.get("time")
        service = entities.get("service")
        
        # Try to parse date and time
        if date_str or time_str:
            try:
                # Combine date and time strings
                datetime_str = f"{date_str or 'today'} {time_str or '12:00'}"
                # Try to parse - this is simplified, in production use more robust parsing
                appointment_time = datetime.now()  # Default to now if parsing fails
                
                # Create appointment
                appointment = Appointment(
                    business_id=business_id,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    appointment_time=appointment_time,
                    service_type=service or "General Checkup",
                    status="scheduled"
                )
                db.add(appointment)
                db.commit()
                db.refresh(appointment)
                print(f"[Voice API] Created appointment {appointment.id} for {customer_phone}")
                appointment_created = True
            except Exception as e:
                print(f"[Voice API] Failed to create appointment: {e}")
                db.rollback()
    
    # Also check if AI response mentions scheduling (fallback)
    if not appointment_created and ("scheduled" in agent_response.lower() or "booked" in agent_response.lower()):
        # AI confirmed appointment in response - create it
        try:
            appointment = Appointment(
                business_id=business_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                appointment_time=datetime.now(),
                service_type="Checkup",
                status="scheduled"
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            print(f"[Voice API] Created appointment {appointment.id} from AI confirmation")
        except Exception as e:
            print(f"[Voice API] Failed to create appointment: {e}")
            db.rollback()
    
    # Add to conversation history
    session["conversation_history"].append({
        "role": "ai",
        "content": agent_response
    })
    
    return {"status": "processed", "text": agent_response}


@router.post("/session/{session_id}/end")
async def end_http_session(session_id: str):
    """End an HTTP session"""
    session_store.end_session(session_id)
    return {"status": "ended"}