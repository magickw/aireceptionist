"""
Voice WebSocket Endpoint
Handles real-time voice communication with Nova 2 Sonic and reasoning
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from typing import Dict, Any, AsyncGenerator, Optional
import json
import asyncio
import base64
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from app.services.nova_reasoning import nova_reasoning
from app.services.nova_sonic import nova_sonic, AudioBuffer, LatencyTracker
from app.core.config import settings as app_settings
from app.api.deps import get_current_business_id, get_current_active_user, get_db
from app.models.models import User, Appointment, Order, OrderItem, MenuItem, CallSession, CalendarIntegration
from sqlalchemy.orm import Session

router = APIRouter()


def parse_natural_datetime(
    date_str: Optional[str], 
    time_str: Optional[str],
    timezone_hint: str = "local"
) -> Optional[datetime]:
    """
    Parse natural language date and time strings into a datetime object.
    
    Examples:
    - date_str="tomorrow", time_str="2pm" -> tomorrow at 14:00
    - date_str="next tuesday", time_str="10:30 am" -> next tuesday at 10:30
    - date_str="today", time_str="3pm" -> today at 15:00
    - date_str="march 15th", time_str="2pm" -> march 15 at 14:00
    - date_str=None, time_str="2pm" -> today at 14:00
    
    Returns None if parsing fails completely.
    """
    now = datetime.now()
    
    # Build combined string
    if date_str and time_str:
        combined = f"{date_str} {time_str}"
    elif date_str:
        combined = date_str
    elif time_str:
        combined = f"today {time_str}"
    else:
        return None
    
    combined = combined.strip().lower()
    
    # Pre-process common patterns
    # Handle "tomorrow" variations
    if "tomorrow" in combined:
        combined = combined.replace("tomorrow", "")
        try:
            parsed_time = date_parser.parse(combined.strip()) if combined.strip() else None
            tomorrow = now + timedelta(days=1)
            if parsed_time:
                return tomorrow.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            return tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
        except:
            return now + timedelta(days=1)
    
    # Handle relative days like "in 2 days", "in 3 days"
    import re
    in_days_match = re.search(r'in (\d+) days?', combined)
    if in_days_match:
        days = int(in_days_match.group(1))
        future_date = now + timedelta(days=days)
        combined = combined.replace(in_days_match.group(0), "").strip()
        if combined:
            try:
                parsed_time = date_parser.parse(combined)
                return future_date.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            except:
                pass
        return future_date.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Handle "next [day]" patterns
    next_day_match = re.search(r'next (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', combined)
    if next_day_match:
        day_name = next_day_match.group(1)
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target_weekday = weekdays.index(day_name)
        current_weekday = now.weekday()
        days_ahead = (target_weekday - current_weekday + 7) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week's same day
        target_date = now + timedelta(days=days_ahead)
        
        # Try to extract time from remaining text
        remaining = combined.replace(next_day_match.group(0), "").strip()
        if remaining:
            try:
                parsed_time = date_parser.parse(remaining)
                return target_date.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            except:
                pass
        return target_date.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Handle "this [day]" patterns
    this_day_match = re.search(r'this (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', combined)
    if this_day_match:
        day_name = this_day_match.group(1)
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target_weekday = weekdays.index(day_name)
        current_weekday = now.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead < 0:
            days_ahead += 7
        target_date = now + timedelta(days=days_ahead)
        
        remaining = combined.replace(this_day_match.group(0), "").strip()
        if remaining:
            try:
                parsed_time = date_parser.parse(remaining)
                return target_date.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            except:
                pass
        return target_date.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Handle "today"
    if "today" in combined:
        remaining = combined.replace("today", "").strip()
        if remaining:
            try:
                parsed_time = date_parser.parse(remaining)
                return now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            except:
                pass
        return now.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Try general dateutil parsing
    try:
        # Use fuzzy parsing to handle natural language
        parsed = date_parser.parse(combined, fuzzy=True)
        # If no year was specified and the date is in the past, assume next year
        if parsed.year == now.year and parsed < now:
            # Check if the parsed date seems like it should be in the future
            if parsed.month < now.month or (parsed.month == now.month and parsed.day < now.day):
                parsed = parsed.replace(year=now.year + 1)
        return parsed
    except Exception as e:
        print(f"[Date Parser] Failed to parse '{combined}': {e}")
    
    # Final fallback - if only time was provided, use today
    if time_str and not date_str:
        try:
            parsed_time = date_parser.parse(time_str)
            return now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
        except:
            pass
    
    return None


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


async def handle_tool_use(
    tool_name: str,
    tool_input: Dict[str, Any],
    ws_session: Dict[str, Any],
    business_id: int,
    business_context: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """
    Execute business logic when Nova Sonic invokes a tool.
    Maps streaming tool calls to existing business operations.
    """
    if tool_name == "bookAppointment":
        date_str = tool_input.get("date")
        time_str = tool_input.get("time")
        customer_name = tool_input.get("customer_name", ws_session.get("customer_name", "Unknown"))
        customer_phone = tool_input.get("customer_phone", ws_session.get("customer_phone", "Unknown"))
        service = tool_input.get("service", "General")

        ws_session["customer_name"] = customer_name
        ws_session["customer_phone"] = customer_phone

        appointment_time = parse_natural_datetime(date_str, time_str)
        if not appointment_time:
            return {"success": False, "message": "Could not parse the date and time."}

        try:
            from app.services.calendar_service import calendar_service
            end_time = appointment_time + timedelta(hours=1)

            result = await calendar_service.check_and_book_appointment(
                business_id=business_id,
                start_time=appointment_time,
                end_time=end_time,
                customer_name=customer_name,
                customer_phone=customer_phone,
                service=service,
                db=db,
            )
            if result["success"]:
                date_fmt = appointment_time.strftime("%B %d")
                time_fmt = appointment_time.strftime("%I:%M %p")
                return {"success": True, "message": f"Appointment booked for {date_fmt} at {time_fmt}."}
            else:
                return {"success": False, "message": result.get("message", "Time slot not available.")}
        except Exception as e:
            print(f"[Tool] bookAppointment error: {e}")
            return {"success": False, "message": "Failed to book appointment."}

    elif tool_name == "checkAvailability":
        date_str = tool_input.get("date")
        time_str = tool_input.get("time")
        appointment_time = parse_natural_datetime(date_str, time_str)
        if not appointment_time:
            return {"available": False, "message": "Could not parse the date and time."}

        try:
            from app.services.calendar_service import calendar_service
            end_time = appointment_time + timedelta(hours=1)

            integration = db.query(CalendarIntegration).filter(
                CalendarIntegration.business_id == business_id,
                CalendarIntegration.status == "active",
            ).first()

            is_available = True
            if integration:
                availability = await calendar_service.check_availability(
                    integration, appointment_time, end_time, db
                )
                is_available = availability.get("available", False)
            else:
                from app.services.calendar_service import calendar_service as cal_svc
                db_conflicts = cal_svc.check_db_conflicts(business_id, appointment_time, end_time, db)
                is_available = not db_conflicts

            date_fmt = appointment_time.strftime("%B %d")
            time_fmt = appointment_time.strftime("%I:%M %p")
            if is_available:
                return {"available": True, "message": f"{date_fmt} at {time_fmt} is available."}
            else:
                return {"available": False, "message": f"{date_fmt} at {time_fmt} is not available."}
        except Exception as e:
            print(f"[Tool] checkAvailability error: {e}")
            return {"available": False, "message": "Could not check availability."}

    elif tool_name == "placeOrder":
        items = tool_input.get("items", [])
        delivery_method = tool_input.get("delivery_method")
        if delivery_method:
            ws_session["delivery_method"] = delivery_method

        menu = business_context.get("menu", [])
        added = []
        for req_item in items:
            req_name = req_item.get("name", "").lower()
            qty = req_item.get("quantity", 1)
            for menu_entry in menu:
                if req_name in menu_entry.get("name", "").lower() or menu_entry.get("name", "").lower() in req_name:
                    existing = next(
                        (i for i in ws_session["order_items"] if i["name"].lower() == menu_entry["name"].lower()),
                        None,
                    )
                    if not existing:
                        ws_session["order_items"].append({
                            "name": menu_entry["name"],
                            "price": menu_entry.get("price", 0),
                            "quantity": qty,
                            "menu_item_id": menu_entry.get("id"),
                        })
                        added.append(f"{qty}x {menu_entry['name']}")
                    break

        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in ws_session["order_items"])
        return {
            "success": True,
            "added": added,
            "total": total,
            "message": f"Added {', '.join(added)}. Total: ${total:.2f}.",
        }

    elif tool_name == "confirmOrder":
        if not ws_session.get("order_items"):
            return {"success": False, "message": "No items in order."}

        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in ws_session["order_items"])
        items_list = ", ".join(
            [f"{i.get('quantity', 1)}x {i['name']}" for i in ws_session["order_items"]]
        )
        await _create_order_from_session(ws_session, ws_session.get("_session_id", ""), db)
        ws_session["order_confirmed"] = True
        ws_session["last_order_summary"] = {
            "items": items_list,
            "total": total,
            "delivery_method": ws_session.get("delivery_method", "pickup"),
        }
        ws_session["order_items"] = []
        return {
            "success": True,
            "message": f"Order confirmed: {items_list}. Total: ${total:.2f}.",
        }

    elif tool_name == "transferToHuman":
        return {
            "success": True,
            "transferred": True,
            "reason": tool_input.get("reason", "Customer requested human agent"),
        }

    elif tool_name == "sendDirections":
        address = business_context.get("address", "our location")
        return {"success": True, "address": address}

    elif tool_name == "processPayment":
        amount = tool_input.get("amount", 0)
        return {"success": True, "message": f"Payment link sent for ${amount:.2f}."}

    return {"success": False, "message": f"Unknown tool: {tool_name}"}


async def _run_streaming_relay(
    sonic_session,
    websocket: WebSocket,
    session_id: str,
    ws_session: Dict[str, Any],
    business_id: int,
    business_context: Dict[str, Any],
    conversation_history: list,
    db: Session,
):
    """
    Background task that reads from NovaSonicStreamSession queues
    and relays events to the WebSocket client.
    """
    async def _relay_transcripts():
        while sonic_session.is_active:
            item = await sonic_session.transcript_queue.get()
            if item is None:
                break
            text = item.get("text", "")
            safety_trigger = item.get("safety_trigger")

            conversation_history.append({"role": "customer", "content": text})

            try:
                await websocket.send_json({"type": "transcript", "text": text})
            except Exception:
                break

            if safety_trigger:
                # Safety triggered — send canned response via Polly TTS fallback
                safety_response = safety_trigger.get("reason", "Transferring to human agent.")
                # Synthesize safety response with Polly
                audio_data = await nova_sonic._synthesize_speech(safety_response)
                try:
                    await websocket.send_json({
                        "type": "human_intervention_request",
                        "reason": safety_trigger.get("reason", "Safety trigger"),
                        "context": {"trigger_type": safety_trigger.get("trigger_type")},
                    })
                    await websocket.send_json({
                        "type": "text_chunk",
                        "chunk": safety_response,
                        "is_last": True,
                        "full_text": safety_response,
                    })
                    if audio_data:
                        await websocket.send_json({
                            "type": "audio",
                            "audio": nova_sonic.encode_audio_base64(audio_data),
                            "format": "pcm16",
                            "sample_rate": 16000,
                        })
                except Exception:
                    break

    async def _relay_audio():
        while sonic_session.is_active:
            item = await sonic_session.audio_queue.get()
            if item is None:
                break
            try:
                await websocket.send_json({
                    "type": "audio",
                    "audio": item.get("audio", ""),
                    "format": "pcm16",
                    "sample_rate": item.get("sample_rate", 24000),
                })
            except Exception:
                break

    async def _relay_text():
        accumulated_text = ""
        while sonic_session.is_active:
            item = await sonic_session.text_queue.get()
            if item is None:
                # Session closing — flush any accumulated text
                if accumulated_text:
                    conversation_history.append({"role": "ai", "content": accumulated_text})
                break

            if item.get("turn_complete"):
                # Assistant turn finished — send final signal and record in history
                if accumulated_text:
                    conversation_history.append({"role": "ai", "content": accumulated_text})
                    try:
                        await websocket.send_json({
                            "type": "text_chunk",
                            "chunk": "",
                            "is_last": True,
                            "full_text": accumulated_text,
                        })
                    except Exception:
                        break
                accumulated_text = ""
                continue

            chunk = item.get("chunk", "")
            accumulated_text += chunk
            try:
                await websocket.send_json({
                    "type": "text_chunk",
                    "chunk": chunk,
                    "is_last": False,
                })
            except Exception:
                break

    async def _relay_tools():
        while sonic_session.is_active:
            item = await sonic_session.tool_queue.get()
            if item is None:
                break
            tool_name = item.get("name", "")
            tool_input = item.get("input", {})
            tool_use_id = item.get("tool_use_id", "")

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
                print(f"[Relay] Tool execution error for {tool_name}: {e}")
                result = {"success": False, "message": f"Tool execution failed: {str(e)}"}

            # Send tool result back to the model so it can continue
            await sonic_session.send_tool_result(tool_use_id, result)

            # If transferToHuman, notify WebSocket client
            if tool_name == "transferToHuman":
                try:
                    await websocket.send_json({
                        "type": "human_intervention_request",
                        "reason": tool_input.get("reason", "Transfer requested"),
                        "context": {"tool": tool_name},
                    })
                except Exception:
                    break

    # Run all relays concurrently
    await asyncio.gather(
        _relay_transcripts(),
        _relay_audio(),
        _relay_text(),
        _relay_tools(),
        return_exceptions=True,
    )

    # If the stream died mid-session, notify the client to fall back
    if not sonic_session.is_active:
        try:
            await websocket.send_json({
                "type": "streaming_failed",
                "message": "Voice stream disconnected. Falling back to text mode.",
            })
        except Exception:
            pass


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time voice communication.
    """
    # Accept connection first to avoid immediate timeout/failure
    await websocket.accept()
    
    # Handle authentication manually inside the WebSocket
    from app.api.deps import get_db, get_current_user, get_current_business_id
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Authenticate user with timeout to prevent hanging
        try:
            current_user = await asyncio.wait_for(
                get_current_user(db=db, token_header=None, token_query=token),
                timeout=5.0  # 5 second timeout for authentication
            )
            business_id = await get_current_business_id(current_user=current_user, db=db)
        except asyncio.TimeoutError:
            await websocket.send_json({
                "type": "error",
                "message": "Authentication timeout"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Authentication failed: {str(e)}"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        session_id = f"session_{business_id}_{asyncio.get_event_loop().time()}"
        # Track session state (like order items) for the duration of the WebSocket
        ws_session = {
            "order_items": [],
            "created_at": datetime.utcnow(),
            "business_id": business_id,
            "customer_name": None,
            "customer_phone": None
        }
        
        # Store connection in manager (already accepted)
        manager.active_connections[session_id] = websocket
        manager.audio_buffers[session_id] = AudioBuffer()
        manager.latency_trackers[session_id] = LatencyTracker()
        
        # Create CallSession record in database
        _create_call_session(ws_session, session_id)
        
        # Send connection acknowledgment with audio config
        await manager.send_json(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "Voice connection established with Nova 2 Sonic",
            "audio_config": nova_sonic.get_audio_config()
        })
        
        # Store conversation history for context
        conversation_history = []

        # Track final sentiment for CallSession
        final_sentiment = "neutral"

        # === Audio Buffer for Batch Mode ===
        audio_buffer = b""  # Buffer to accumulate audio chunks in batch mode
        audio_buffer_threshold = 16000 * 2 * 2  # ~2 seconds of 16kHz PCM16 audio

        # === Nova Sonic Streaming Setup ===
        use_streaming = app_settings.NOVA_SONIC_STREAMING_ENABLED
        sonic_session = None
        relay_task = None

        if use_streaming:
            try:
                business_context = await _get_business_context(business_id, db)

                # Fetch knowledge + training context for the prompt
                _knowledge_ctx = ""
                _training_ctx = ""
                if business_context.get("business_id") or business_id:
                    try:
                        from app.services.knowledge_base import knowledge_base_service
                        _knowledge_ctx = await knowledge_base_service.get_relevant_context(
                            query="", business_id=business_id, db=db, max_chars=1500
                        )
                    except Exception:
                        pass
                    try:
                        from app.services.nova_reasoning import get_training_context
                        _training_ctx = await get_training_context(
                            business_id=business_id, db=db
                        )
                    except Exception:
                        pass

                customer_context = {
                    "name": "Unknown",
                    "phone": "Unknown",
                    "call_count": 0,
                    "last_contact": "Never",
                    "satisfaction_score": 0,
                    "preferred_services": [],
                    "complaint_count": 0,
                }

                sonic_session = await nova_sonic.create_streaming_session(
                    session_id=session_id,
                    business_context=business_context,
                    customer_context=customer_context,
                    knowledge_context=_knowledge_ctx,
                    training_context=_training_ctx,
                    db=db,
                )

                ws_session["_session_id"] = session_id

                # Start relay task
                relay_task = asyncio.create_task(
                    _run_streaming_relay(
                        sonic_session=sonic_session,
                        websocket=websocket,
                        session_id=session_id,
                        ws_session=ws_session,
                        business_id=business_id,
                        business_context=business_context,
                        conversation_history=conversation_history,
                        db=db,
                    )
                )

                await manager.send_json(session_id, {
                    "type": "streaming_ready",
                    "message": "Nova Sonic bidirectional streaming active",
                })
                print(f"[Voice WS] Streaming mode initialized successfully for session {session_id}")
            except Exception as e:
                import traceback
                print(f"[Voice WS] Streaming init failed, falling back to batch: {e}")
                print(f"[Voice WS] Traceback: {traceback.format_exc()}")
                use_streaming = False
                sonic_session = None
                # Notify client about fallback
                await manager.send_json(session_id, {
                    "type": "mode_fallback",
                    "message": "Streaming mode unavailable, using batch processing"
                })

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            # Support both 'content' and 'text' for flexibility
            content = data.get("content") or data.get("text") or ""
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
                
                # Build customer context and update ws_session
                customer_context = {
                    "name": context.get("customer_name", "Unknown"),
                    "phone": context.get("customer_phone", "Unknown"),
                    "call_count": context.get("call_count", 0),
                    "last_contact": context.get("last_contact", "Never"),
                    "satisfaction_score": context.get("satisfaction_score", 0),
                    "preferred_services": context.get("preferred_services", []),
                    "complaint_count": context.get("complaint_count", 0)
                }
                
                # Store customer info for order persistence
                if context.get("customer_name"):
                    ws_session["customer_name"] = context.get("customer_name")
                if context.get("customer_phone"):
                    ws_session["customer_phone"] = context.get("customer_phone")
                
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
                
                # Track sentiment for final session summary
                if reasoning_result.get("sentiment"):
                    final_sentiment = reasoning_result.get("sentiment")
                
                # Send agent response - streaming text chunks
                agent_response = reasoning_result.get("suggested_response", "I'm here to help you.")
                
                # Enhance response with actual pricing if customer asked about menu item
                entities = reasoning_result.get("entities", {})
                menu_item = entities.get("menu_item") or entities.get("service")
                
                # Extract customer info from entities OR from message text directly
                content_lower = content.lower() if content else ""
                
                extracted_phone = entities.get("customer_phone")
                extracted_name = entities.get("customer_name")
                
                # FALLBACK: Extract phone number directly from message if not in entities
                if not extracted_phone and content:
                    import re
                    phone_patterns = [
                        r'(?:phone|number|cell|mobile|call|reach)[\s:]*([+]?\d[\d\s\-\(\)]{8,})',
                        r'\b(\d{3}[\s\-]?\d{3}[\s\-]?\d{4})\b',
                        r'\b(\d{10,11})\b',
                    ]
                    for pattern in phone_patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            extracted_phone = re.sub(r'[^\d]', '', match.group(1))
                            if len(extracted_phone) >= 10:
                                print(f"[Voice WS] Extracted phone from message: {extracted_phone}")
                                break
                
                # FALLBACK: Extract name from message
                if not extracted_name and content:
                    import re
                    name_patterns = [
                        r'(?:name is|i am|call me|this is|my name\'s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                        r'(?:name is|i am|call me|this is|my name\'s)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
                    ]
                    for pattern in name_patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            extracted_name = match.group(1).title()
                            print(f"[Voice WS] Extracted name from message: {extracted_name}")
                            break
                
                # Store customer info from entities or extracted values
                if extracted_name:
                    ws_session["customer_name"] = extracted_name
                if extracted_phone:
                    ws_session["customer_phone"] = extracted_phone
                
                # Initialize confirmation tracking if not exists
                if "confirmed_info" not in ws_session:
                    ws_session["confirmed_info"] = {"name": False, "phone": False}
                
                # Intercept if AI is asking for info we already have OR asking for confirmation repeatedly
                if ws_session.get("customer_name") and ws_session.get("customer_phone"):
                    suggested = reasoning_result.get("suggested_response", "")
                    confirmed_info = ws_session.get("confirmed_info", {"name": False, "phone": False})
                    
                    # Detect if customer is confirming their info
                    confirmation_keywords = ["yes", "correct", "that's right", "that is correct", "right", "confirmed", "confirm"]
                    is_confirming = any(kw in content_lower for kw in confirmation_keywords)
                    
                    # If customer is confirming, mark the info as confirmed
                    if is_confirming:
                        if "phone" in suggested.lower() or "number" in suggested.lower():
                            confirmed_info["phone"] = True
                            ws_session["confirmed_info"] = confirmed_info
                        if "name" in suggested.lower():
                            confirmed_info["name"] = True
                            ws_session["confirmed_info"] = confirmed_info
                    
                    asking_for_info = any(phrase in suggested.lower() for phrase in [
                        "your name", "phone number", "confirm your", "provide your"
                    ])
                    
                    # Check if we're asking for something that's already confirmed
                    asking_for_confirmed = False
                    if "phone" in suggested.lower() or "number" in suggested.lower():
                        if confirmed_info.get("phone", False):
                            asking_for_confirmed = True
                    if "name" in suggested.lower():
                        if confirmed_info.get("name", False):
                            asking_for_confirmed = True
                    
                    if asking_for_info and asking_for_confirmed:
                        # Stop asking - info is already confirmed, now actually check availability
                        try:
                            from app.services.calendar_service import calendar_service
                            from app.models.models import CalendarIntegration
                            
                            # Parse the confirmed date and time
                            date_str = confirmed_info.get("date") or confirmed_info.get("preferred_date")
                            time_str = confirmed_info.get("time") or confirmed_info.get("preferred_time")
                            appointment_time = parse_natural_datetime(date_str, time_str)
                            
                            if appointment_time:
                                end_time = appointment_time + timedelta(hours=1)
                                
                                # Check availability immediately
                                integration = db.query(CalendarIntegration).filter(
                                    CalendarIntegration.business_id == business_id,
                                    CalendarIntegration.status == "active"
                                ).first()
                                
                                is_available = True
                                if integration:
                                    availability = await calendar_service.check_availability(integration, appointment_time, end_time, db)
                                    is_available = availability.get("available", False)
                                else:
                                    db_conflicts = calendar_service.check_db_conflicts(business_id, appointment_time, end_time, db)
                                    is_available = not db_conflicts
                                
                                date_fmt = appointment_time.strftime("%B %d")
                                time_fmt = appointment_time.strftime("%I:%M %p")
                                
                                if is_available:
                                    # Book it immediately since all info is confirmed
                                    result = await calendar_service.check_and_book_appointment(
                                        business_id=business_id,
                                        start_time=appointment_time,
                                        end_time=end_time,
                                        customer_name=ws_session.get("customer_name", "Unknown"),
                                        customer_phone=ws_session.get("customer_phone", "Unknown"),
                                        service=confirmed_info.get("service") or confirmed_info.get("service_type") or "General Checkup",
                                        db=db
                                    )
                                    
                                    if result["success"]:
                                        reasoning_result["suggested_response"] = f"Great! I've checked and {date_fmt} at {time_fmt} is available. I've booked your appointment. We'll see you then!"
                                    else:
                                        reasoning_result["suggested_response"] = f"I've checked availability, but there's an issue booking. {result.get('message', 'Please try a different time.')}"
                                else:
                                    # Not available, suggest alternatives
                                    reasoning_result["suggested_response"] = f"I've checked availability, but {date_fmt} at {time_fmt} is not available. Would you like me to check another time?"
                            else:
                                reasoning_result["suggested_response"] = f"Great, thank you {ws_session['customer_name']}! I need a specific date and time to check availability."
                        except Exception as e:
                            print(f"[Voice API WS] Availability check error: {e}")
                            reasoning_result["suggested_response"] = f"Great, thank you {ws_session['customer_name']}! Let me check availability for your appointment."
                        agent_response = reasoning_result["suggested_response"]
                        print(f"[Voice API WS] Info confirmed, checking availability: {confirmed_info}")
                    elif asking_for_info:
                        # Still collecting info
                        reasoning_result["suggested_response"] = f"Great, thank you {ws_session['customer_name']}! Let me check availability for your appointment."
                        agent_response = reasoning_result["suggested_response"]
                
                # --- Pending appointment confirmation ---
                # If AI previously asked "Would you like me to book?" and user confirms,
                # actually create the appointment using the stored details.
                if ws_session.get("pending_appointment"):
                    confirm_kw = ["yes", "yeah", "yep", "sure", "please", "book", "confirm", "go ahead", "do it", "ok", "okay"]
                    decline_kw = ["no", "nah", "cancel", "don't", "different", "other", "change", "another"]
                    user_confirms = any(kw in content_lower for kw in confirm_kw) and not any(kw in content_lower for kw in decline_kw)
                    user_declines = any(kw in content_lower for kw in decline_kw)

                    if user_confirms:
                        pending = ws_session.pop("pending_appointment")
                        try:
                            from app.services.calendar_service import calendar_service
                            result = await calendar_service.check_and_book_appointment(
                                business_id=business_id,
                                start_time=pending["start_time"],
                                end_time=pending["end_time"],
                                customer_name=ws_session.get("customer_name", "Unknown"),
                                customer_phone=ws_session.get("customer_phone", "Unknown"),
                                service=pending.get("service", "General Checkup"),
                                db=db,
                            )
                            if result["success"]:
                                date_fmt = pending["start_time"].strftime("%B %d")
                                time_fmt = pending["start_time"].strftime("%I:%M %p")
                                agent_response = f"Great! I've booked your appointment for {date_fmt} at {time_fmt}. We'll see you then!"
                                print(f"[Voice WS] Created appointment {result['appointment'].id} for {ws_session.get('customer_phone')} at {pending['start_time']}")
                            else:
                                agent_response = f"I'm sorry, I couldn't book that appointment. {result.get('message', 'Please try a different time.')}"
                        except Exception as e:
                            print(f"[Voice WS] Pending appointment booking error: {e}")
                            agent_response = "I'm having trouble booking that appointment right now. Could you please try again?"
                    elif user_declines:
                        ws_session.pop("pending_appointment", None)
                        agent_response = "No problem! Would you like to check a different time?"

                # Handle specific actions from reasoning (skip if pending appointment already handled)
                selected_action = reasoning_result.get("selected_action")
                pending_handled = "pending_appointment" not in ws_session and (
                    "I've booked your appointment" in agent_response or "I couldn't book" in agent_response
                )
                menu_item = entities.get("menu_item") or entities.get("service")
                quantity = entities.get("quantity", 1) if isinstance(entities.get("quantity"), int) else 1

                # Detect clarification phrases - customer is NOT adding items
                # (content_lower is already defined above)
                clarification_phrases = [
                    "i just wanted", "i didn't say", "i meant", "what i meant",
                    "i already", "already ordered", "don't add", "didn't want to add",
                    "no i didn't", "that's not what", "i said i wanted", "clarify",
                    "i was just saying", "just clarifying", "i meant to say"
                ]
                is_clarification = any(phrase in content_lower for phrase in clarification_phrases)

                # Handle PLACE_ORDER action - ONLY when explicitly triggered by the model
                if pending_handled:
                    pass  # Appointment already created from pending confirmation
                elif selected_action == "PLACE_ORDER" and not is_clarification:
                    if menu_item and business_context.get("menu"):
                        menu_lower = menu_item.lower()
                        for item in business_context.get("menu", []):
                            if menu_lower in item.get("name", "").lower() or item.get("name", "").lower() in menu_lower:
                                # Check if item already in order (avoid duplicates)
                                existing = next((i for i in ws_session["order_items"] if i["name"].lower() == item["name"].lower()), None)
                                if existing:
                                    # Item already exists - don't add again
                                    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in ws_session["order_items"])
                                    agent_response = f"You already have {existing.get('quantity', 1)}x {item['name']} in your order. Your total is ${total:.2f}. Would you like to add more, or shall I confirm your order?"
                                else:
                                    order_entry = {
                                        "name": item["name"],
                                        "price": item.get("price", 0),
                                        "quantity": quantity,
                                        "menu_item_id": item.get("id")
                                    }
                                    ws_session["order_items"].append(order_entry)
                                    
                                    # Ask for delivery method
                                    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in ws_session["order_items"])
                                    agent_response = f"Got it! Added {quantity}x {item['name']} to your order. Your current total is ${total:.2f}. Would you like pickup or delivery?"
                                break
                
                # Handle clarification about existing order
                elif is_clarification and ws_session.get("order_items"):
                    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in ws_session["order_items"])
                    items_list = ", ".join([f"{i.get('quantity', 1)}x {i['name']}" for i in ws_session["order_items"]])
                    agent_response = f"I understand. You have: {items_list}. Your total is ${total:.2f}. Would you like pickup or delivery?"
                
                elif selected_action == "CONFIRM_ORDER":
                    # Check for missing required info first
                    if ws_session["order_items"]:
                        missing_info = []
                        if not ws_session.get("customer_name"):
                            missing_info.append("name")
                        if not ws_session.get("customer_phone"):
                            missing_info.append("phone number")
                        
                        # If missing info, ask for it
                        if missing_info:
                            total = sum(item.get("price", 0) * item.get("quantity", 1) for item in ws_session["order_items"])
                            items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in ws_session["order_items"]])
                            
                            if len(missing_info) == 2:
                                agent_response = f"Almost there! For your order of {items_list} (${total:.2f}), I'll need your name and phone number."
                            else:
                                agent_response = f"Almost there! What's your {missing_info[0]} for the order?"
                        else:
                            # All info collected - proceed
                            total = sum(item.get("price", 0) * item.get("quantity", 1) for item in ws_session["order_items"])
                            items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in ws_session["order_items"]])
                            delivery_text = f" for {ws_session.get('delivery_method', 'pickup')}" if ws_session.get("delivery_method") else " for pickup"
                            agent_response = f"Perfect! I've confirmed your order: {items_list}. Your total is ${total:.2f}{delivery_text}. We'll have it ready for you. Thank you!"
                            
                            await _create_order_from_session(ws_session, session_id, db)
                            
                            # Store order summary for context
                            ws_session["order_confirmed"] = True
                            ws_session["last_order_summary"] = {
                                "items": items_list,
                                "total": total,
                                "delivery_method": ws_session.get("delivery_method", "pickup")
                            }
                            ws_session["order_items"] = []
                    else:
                        # Check if we just completed an order
                        if ws_session.get("order_confirmed") and ws_session.get("last_order_summary"):
                            last_order = ws_session["last_order_summary"]
                            agent_response = f"You're welcome! Your order ({last_order['items']}) will be ready for {last_order.get('delivery_method', 'pickup')}. Is there anything else I can help you with?"
                        else:
                            agent_response = f"I don't see any items in your order yet. Would you like to add anything?"
                
                elif selected_action == "SEND_DIRECTIONS":
                    address = business_context.get("address", "our location")
                    landmark = entities.get("landmark", "")
                    landmark_text = f" near {landmark}" if landmark else ""
                    agent_response = f"We are located at {address}{landmark_text}. {agent_response}"
                
                elif selected_action == "PAYMENT_PROCESS":
                    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in ws_session["order_items"]) if ws_session["order_items"] else 0
                    if total > 0:
                        agent_response = f"I've initiated a secure payment process for your total of ${total:.2f}. I'm sending a secure link to your phone now. {agent_response}"
                    else:
                        agent_response = f"I'd be happy to help with that payment. Could you please confirm what you'd like to pay for? {agent_response}"
                
                elif selected_action == "HUMAN_INTERVENTION":
                    # Send intervention request event
                    await manager.send_json(session_id, {
                        "type": "human_intervention_request",
                        "reason": reasoning_result.get("safety_reason", "Unknown safety trigger"),
                        "context": {
                            "intent": reasoning_result.get("intent"),
                            "confidence": reasoning_result.get("confidence"),
                            "risk": reasoning_result.get("escalation_risk")
                        }
                    })
                
                elif selected_action == "CREATE_ORDER":
                    if ws_session["order_items"]:
                        total_amount = sum(item.get("price", 0) * item.get("quantity", 1) for item in ws_session["order_items"])
                        items_summary = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in ws_session["order_items"]])
                        agent_response = f"Got it! I'm placing your order now for {items_summary}. Your total is ${total_amount:.2f}. Thank you!"
                        await _create_order_from_session(ws_session, session_id, db)
                    else:
                        agent_response = "I don't have any items in your order. What would you like to get?"
                
                elif selected_action == "CREATE_APPOINTMENT":
                    # Handle appointment booking in WebSocket
                    date_str = entities.get("date") or entities.get("preferred_date")
                    time_str = entities.get("time") or entities.get("preferred_time")
                    service = entities.get("service") or entities.get("service_type")
                    
                    # Parse date/time
                    appointment_time = parse_natural_datetime(date_str, time_str)
                    
                    if appointment_time:
                        try:
                            from app.services.calendar_service import calendar_service
                            from app.models.models import CalendarIntegration, Appointment
                            
                            end_time = appointment_time + timedelta(hours=1)
                            
                            # Check for calendar integration
                            integration = db.query(CalendarIntegration).filter(
                                CalendarIntegration.business_id == business_id,
                                CalendarIntegration.status == "active"
                            ).first()
                            
                            is_available = True
                            if integration:
                                availability = await calendar_service.check_availability(integration, appointment_time, end_time, db)
                                is_available = availability.get("available", False)
                            else:
                                # No calendar integration - check local DB conflicts
                                db_conflicts = calendar_service.check_db_conflicts(business_id, appointment_time, end_time, db)
                                is_available = not db_conflicts
                            
                            if not is_available:
                                date_fmt = appointment_time.strftime("%B %d")
                                time_fmt = appointment_time.strftime("%I:%M %p")
                                agent_response = f"I'm sorry, but {date_fmt} at {time_fmt} is not available. Would you like me to check another time?"
                            else:
                                # Book the appointment
                                result = await calendar_service.check_and_book_appointment(
                                    business_id=business_id,
                                    start_time=appointment_time,
                                    end_time=end_time,
                                    customer_name=ws_session.get("customer_name", "Unknown"),
                                    customer_phone=ws_session.get("customer_phone", "Unknown"),
                                    service=service or "General Checkup",
                                    db=db
                                )
                                
                                if result["success"]:
                                    date_fmt = appointment_time.strftime("%B %d")
                                    time_fmt = appointment_time.strftime("%I:%M %p")
                                    agent_response = f"Great! I've booked your appointment for {date_fmt} at {time_fmt}. We'll see you then!"
                                    print(f"[Voice WS] Created appointment {result['appointment'].id} for {ws_session.get('customer_phone')} at {appointment_time}")
                                else:
                                    agent_response = f"I'm sorry, I couldn't book that appointment. {result.get('message', 'Please try a different time.')}"
                        except Exception as e:
                            print(f"[Voice WS] Appointment booking error: {e}")
                            agent_response = f"I'm having trouble booking that appointment right now. Could you please try again or call us directly?"
                    else:
                        agent_response = "I'd be happy to book an appointment for you. What date and time would you prefer?"
                
                # Also handle when customer asks about availability (not just CREATE_APPOINTMENT action)
                # Check if message mentions availability or booking with a specific time
                elif "available" in content_lower or "book" in content_lower or "appointment" in content_lower:
                    date_str = entities.get("date") or entities.get("preferred_date")
                    time_str = entities.get("time") or entities.get("preferred_time")
                    
                    appointment_time = parse_natural_datetime(date_str, time_str)
                    
                    if appointment_time and ("available" in content_lower or time_str):
                        try:
                            from app.services.calendar_service import calendar_service
                            from app.models.models import CalendarIntegration
                            
                            end_time = appointment_time + timedelta(hours=1)
                            
                            # Check availability
                            integration = db.query(CalendarIntegration).filter(
                                CalendarIntegration.business_id == business_id,
                                CalendarIntegration.status == "active"
                            ).first()
                            
                            is_available = True
                            if integration:
                                availability = await calendar_service.check_availability(integration, appointment_time, end_time, db)
                                is_available = availability.get("available", False)
                            else:
                                db_conflicts = calendar_service.check_db_conflicts(business_id, appointment_time, end_time, db)
                                is_available = not db_conflicts
                            
                            date_fmt = appointment_time.strftime("%B %d")
                            time_fmt = appointment_time.strftime("%I:%M %p")
                            
                            if is_available:
                                # Check if customer wants to book or just checking
                                if "book" in content_lower or "schedule" in content_lower or "make an appointment" in content_lower:
                                    # Book it
                                    result = await calendar_service.check_and_book_appointment(
                                        business_id=business_id,
                                        start_time=appointment_time,
                                        end_time=end_time,
                                        customer_name=ws_session.get("customer_name", "Unknown"),
                                        customer_phone=ws_session.get("customer_phone", "Unknown"),
                                        service=entities.get("service") or "General Checkup",
                                        db=db
                                    )
                                    
                                    if result["success"]:
                                        agent_response = f"Perfect! I've booked your appointment for {date_fmt} at {time_fmt}. We'll see you then!"
                                    else:
                                        agent_response = f"I'm sorry, I couldn't complete the booking. Would you like to try a different time?"
                                else:
                                    # Just checking availability - store pending appointment
                                    agent_response = f"Yes, {date_fmt} at {time_fmt} is available! Would you like me to book that for you?"
                                    ws_session["pending_appointment"] = {
                                        "start_time": appointment_time,
                                        "end_time": end_time,
                                        "service": entities.get("service") or entities.get("service_type") or "General Checkup",
                                    }
                            else:
                                agent_response = f"I'm sorry, {date_fmt} at {time_fmt} is not available. Would you like me to check another time?"
                        except Exception as e:
                            print(f"[Voice WS] Availability check error: {e}")
                
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
                
            elif message_type == "audio_start":
                # Mark beginning of user voice turn (streaming mode)
                if use_streaming and sonic_session and sonic_session.is_active:
                    await sonic_session.start_user_turn()
                elif use_streaming and sonic_session and not sonic_session.is_active:
                    # Stream died — tell client to switch modes
                    use_streaming = False
                    await manager.send_json(session_id, {
                        "type": "streaming_failed",
                        "message": "Voice stream disconnected. Please use text input.",
                    })

            elif message_type == "audio_stop":
                if use_streaming and sonic_session and sonic_session.is_active:
                    # STREAMING PATH: end user turn triggers STT + model response
                    await sonic_session.end_user_turn()
                    # Send latency metrics after turn completes
                    await asyncio.sleep(0.5)  # brief wait for metrics to populate
                    metrics = sonic_session.latency.get_metrics()
                    if metrics:
                        await manager.send_json(session_id, {
                            "type": "latency_metrics",
                            "metrics": metrics,
                        })
                elif audio_buffer:
                    # BATCH FALLBACK: flush remaining audio buffer on stop
                    try:
                        tracker = manager.latency_trackers.get(session_id)
                        if tracker:
                            tracker.start()

                        buffered_audio = audio_buffer
                        audio_buffer = b""

                        async for response in nova_sonic.process_audio_stream(
                            _generate_audio_chunks([buffered_audio]),
                            {
                                "business_context": await _get_business_context(business_id),
                                "customer_context": context,
                            }
                        ):
                            if response["type"] == "transcript":
                                conversation_history.append({
                                    "role": "customer",
                                    "content": response["text"],
                                })
                                await manager.send_json(session_id, {
                                    "type": "transcript",
                                    "text": response["text"],
                                })
                            elif response["type"] == "text_response":
                                conversation_history.append({
                                    "role": "ai",
                                    "content": response["text"],
                                })
                                await manager.send_json(session_id, {
                                    "type": "agent_response",
                                    "text": response["text"],
                                })
                            elif response["type"] == "audio":
                                audio_base64 = nova_sonic.encode_audio_base64(response["data"])
                                await manager.send_json(session_id, {
                                    "type": "audio",
                                    "audio": audio_base64,
                                    "format": "pcm16",
                                    "sample_rate": 16000,
                                })
                            elif response["type"] == "complete":
                                if tracker:
                                    tracker.end()
                                    metrics = tracker.get_metrics()
                                    await manager.send_json(session_id, {
                                        "type": "latency_metrics",
                                        "metrics": metrics,
                                    })
                            elif response["type"] == "error":
                                await manager.send_json(session_id, {
                                    "type": "error",
                                    "message": response["message"],
                                })
                    except Exception as e:
                        print(f"[Voice WS] Batch audio_stop processing error: {e}")
                        await manager.send_json(session_id, {
                            "type": "error",
                            "message": f"Audio processing error: {str(e)}",
                        })

            elif message_type == "audio":
                if use_streaming and sonic_session and sonic_session.is_active:
                    # STREAMING PATH: forward audio chunk immediately
                    try:
                        audio_data = nova_sonic.decode_audio_base64(content)
                        await sonic_session.send_audio_chunk(audio_data)
                    except Exception as e:
                        await manager.send_json(session_id, {
                            "type": "error",
                            "message": f"Streaming audio error: {str(e)}"
                        })
                else:
                    # BATCH FALLBACK: buffer audio and process when enough accumulated
                    try:
                        # Decode base64 audio
                        audio_data = nova_sonic.decode_audio_base64(content)
                        
                        # Add to buffer
                        audio_buffer += audio_data
                        print(f"[Voice WS] Audio buffer: {len(audio_buffer)} bytes (threshold: {audio_buffer_threshold})")
                        
                        # Only process when we have enough audio
                        if len(audio_buffer) < audio_buffer_threshold:
                            # Send acknowledgment that we're listening
                            await manager.send_json(session_id, {
                                "type": "listening",
                                "buffer_size": len(audio_buffer),
                                "threshold": audio_buffer_threshold
                            })
                            continue
                        
                        # Start latency tracking
                        tracker = manager.latency_trackers.get(session_id)
                        if tracker:
                            tracker.start()

                        # Process buffered audio
                        buffered_audio = audio_buffer
                        audio_buffer = b""  # Clear buffer after processing

                        # Process audio stream
                        async for response in nova_sonic.process_audio_stream(
                            _generate_audio_chunks([buffered_audio]),
                            {
                                "business_context": await _get_business_context(business_id),
                                "customer_context": context
                            }
                        ):
                            if response["type"] == "transcript":
                                conversation_history.append({
                                    "role": "customer",
                                    "content": response["text"]
                                })
                                await manager.send_json(session_id, {
                                    "type": "transcript",
                                    "text": response["text"]
                                })

                            elif response["type"] == "text_response":
                                conversation_history.append({
                                    "role": "ai",
                                    "content": response["text"]
                                })
                                await manager.send_json(session_id, {
                                    "type": "agent_response",
                                    "text": response["text"]
                                })

                            elif response["type"] == "audio":
                                audio_base64 = nova_sonic.encode_audio_base64(response["data"])
                                await manager.send_json(session_id, {
                                    "type": "audio",
                                    "audio": audio_base64,
                                    "format": "pcm16",
                                    "sample_rate": 16000
                                })

                            elif response["type"] == "complete":
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
                        print(f"[Voice WS] Batch audio processing error: {e}")
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
                # End the call - save session and order
                # Clean up streaming session
                if sonic_session:
                    await sonic_session.close()
                if relay_task and not relay_task.done():
                    relay_task.cancel()
                summary = " | ".join([f"{m['role']}: {m['content'][:100]}" for m in conversation_history[-5:]]) if conversation_history else ""
                _end_call_session(ws_session, session_id, summary, final_sentiment)
                # Get a DB session for saving
                from app.api.deps import get_db
                db_gen = get_db()
                db = next(db_gen)
                try:
                    await _save_confirmed_order(ws_session, session_id, db)
                finally:
                    db.close()
                await manager.send_json(session_id, {
                    "type": "call_ended",
                    "message": "Call ended"
                })
                break
    
    except WebSocketDisconnect:
        # Clean up streaming session
        if sonic_session:
            await sonic_session.close()
        if relay_task and not relay_task.done():
            relay_task.cancel()
        # Get a new DB session for cleanup
        db = next(get_db())
        summary = " | ".join([f"{m['role']}: {m['content'][:100]}" for m in conversation_history[-5:]]) if 'conversation_history' in dir() and conversation_history else ""
        _end_call_session(ws_session, session_id, summary, final_sentiment if 'final_sentiment' in dir() else "neutral")
        await _save_confirmed_order(ws_session, session_id, db)
        manager.disconnect(session_id)
        db.close()
    except Exception as e:
        # Clean up streaming session
        if sonic_session:
            await sonic_session.close()
        if relay_task and not relay_task.done():
            relay_task.cancel()
        # Get a new DB session for cleanup
        db = next(get_db())
        await manager.send_json(session_id, {
            "type": "error",
            "message": f"Error: {str(e)}"
        })
        # Try to save session and order even on error
        summary = " | ".join([f"{m['role']}: {m['content'][:100]}" for m in conversation_history[-5:]]) if 'conversation_history' in dir() and conversation_history else ""
        _end_call_session(ws_session, session_id, summary, final_sentiment if 'final_sentiment' in dir() else "neutral")
        await _save_confirmed_order(ws_session, session_id, db)
        manager.disconnect(session_id)
        db.close()



async def _save_confirmed_order(ws_session: Dict[str, Any], session_id: str, db: Session) -> None:
    """Save a confirmed order to the database."""
    if not ws_session.get("order_confirmed") or not ws_session.get("order_items"):
        return
    
    await _create_order_from_session(ws_session, session_id, db)


async def _create_order_from_session(ws_session: Dict[str, Any], session_id: str, db: Session) -> None:
    """Helper function to create an order and its items from session data."""
    if not ws_session.get("order_items"):
        return
    
    try:
        business_id = ws_session.get("business_id")
        if not business_id:
            return
        
        # Calculate total
        total = sum(
            item.get("price", 0) * item.get("quantity", 1) 
            for item in ws_session["order_items"]
        )
        
        # Create order
        order = Order(
            business_id=business_id,
            call_session_id=session_id,
            customer_name=ws_session.get("customer_name"),
            customer_phone=ws_session.get("customer_phone"),
            status="confirmed",
            total_amount=total,
            confirmed_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()  # Get order ID
        
        # Create order items
        for item in ws_session["order_items"]:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item.get("menu_item_id"),
                item_name=item["name"],
                quantity=item.get("quantity", 1),
                unit_price=item.get("price", 0)
            )
            db.add(order_item)
        
        db.commit()
        print(f"Order {order.id} created successfully for business {business_id}")
        ws_session["order_items"] = [] # Clear items after successful order
    except Exception as e:
        print(f"Failed to create order from session: {e}")


def _create_call_session(ws_session: Dict[str, Any], session_id: str) -> None:
    """Create a CallSession record in the database."""
    try:
        from app.api.deps import get_db
        gen = get_db()
        db = next(gen)
        
        business_id = ws_session.get("business_id")
        if not business_id:
            return
        
        call_session = CallSession(
            id=session_id,
            business_id=business_id,
            customer_name=ws_session.get("customer_name"),
            customer_phone=ws_session.get("customer_phone"),
            status="active"
        )
        db.add(call_session)
        db.commit()
        ws_session["db_session_created"] = True
    except Exception as e:
        print(f"Failed to create call session: {e}")
    finally:
        try:
            db.close()
        except:
            pass


def _end_call_session(ws_session: Dict[str, Any], session_id: str, summary: str = None, sentiment: str = None) -> None:
    """Update CallSession record when call ends."""
    try:
        from app.api.deps import get_db
        gen = get_db()
        db = next(gen)
        
        call_session = db.query(CallSession).filter(CallSession.id == session_id).first()
        if call_session:
            call_session.status = "ended"
            call_session.ended_at = datetime.utcnow()
            if call_session.started_at:
                call_session.duration_seconds = int((datetime.utcnow() - call_session.started_at).total_seconds())
            if summary:
                call_session.summary = summary
            if sentiment:
                call_session.sentiment = sentiment
            db.commit()
    except Exception as e:
        print(f"Failed to end call session: {e}")
    finally:
        try:
            db.close()
        except:
            pass


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
        "address": business.address or "Our business location",
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
            "order_items": [],  # Track items ordered with quantity
            "order_confirmed": False,  # Track if order was confirmed
            "delivery_method": None,  # "pickup" or "delivery"
            "customer_name": None,  # Customer name for order
            "price_mentioned": False,  # Track if price was already mentioned
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
    
    # Use session as http_session for compatibility with legacy code blocks
    http_session = session
    
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
    
    # Define suggested response early for use in logic blocks
    suggested = reasoning_result.get("suggested_response", "")
    
    # Add reasoning chain event
    session_store.add_event(session_id, {
        "type": "reasoning_chain",
        "data": reasoning_result.get("reasoning_chain", [])
    })
    
    # ===== GOVERNANCE ENGINE INTEGRATION =====
    # Determine governance tier based on business type, intent, confidence, and action
    from app.services.business_templates import BusinessTypeTemplate, GovernanceTier
    business_type = business_context.get('type', 'general')
    detected_intent = reasoning_result.get("intent", "")
    confidence = reasoning_result.get("confidence", 0.5)
    proposed_action = reasoning_result.get("selected_action", "")
    entities = reasoning_result.get("entities", {})
    
    governance_tier = BusinessTypeTemplate.get_governance_tier(
        business_type=business_type,
        intent=detected_intent,
        confidence=confidence,
        action=proposed_action,
        entities=entities
    )
    execution_policy = BusinessTypeTemplate.get_execution_policy(governance_tier)
    
    # Log governance decision
    print(f"[Voice API] Governance: tier={governance_tier}, action={proposed_action}, confidence={confidence:.2f}")
    
    # Add governance info to reasoning complete event
    # Add reasoning complete event
    session_store.add_event(session_id, {
        "type": "reasoning_complete",
        "data": {
            "intent": detected_intent,
            "confidence": confidence,
            "selected_action": proposed_action,
            "sentiment": reasoning_result.get("sentiment"),
            "escalation_risk": reasoning_result.get("escalation_risk"),
            "governance_tier": governance_tier,
            "requires_confirmation": execution_policy.get("requires_confirmation", False),
            "requires_human_approval": execution_policy.get("requires_human_approval", False)
        }
    })
    
    # Handle governance tier actions
    if governance_tier == GovernanceTier.ESCALATE_IMMEDIATE:
        # Immediate transfer to human
        session_store.add_event(session_id, {
            "type": "human_intervention_request",
            "reason": f"Governance tier: {governance_tier}",
            "context": {
                "intent": detected_intent,
                "confidence": confidence,
                "risk": reasoning_result.get("escalation_risk"),
                "governance_tier": governance_tier
            }
        })
        agent_response = reasoning_result.get("suggested_response", "Let me transfer you to someone who can better assist you.")
        if execution_policy.get("provide_safety_instructions"):
            agent_response = "I'm connecting you with our team right away. In the meantime, " + agent_response
        
        # Add agent response event
        session_store.add_event(session_id, {
            "type": "agent_response",
            "text": agent_response,
            "reasoning": reasoning_result
        })
        
        # Create audit record
        audit_record = BusinessTypeTemplate.create_audit_record(
            business_type=business_type,
            session_id=session_id,
            intent=detected_intent,
            action=proposed_action,
            governance_tier=governance_tier,
            confidence=confidence,
            entities=entities,
            collected_data=http_session if http_session else {},
            executed=False,
            human_approved=False
        )
        print(f"[Audit] {audit_record['log_level'].upper()}: {audit_record}")
        
        # Add to conversation history
        session["conversation_history"].append({
            "role": "ai",
            "content": agent_response
        })
        return {"status": "processed", "text": agent_response, "governance_tier": governance_tier}
    
    elif governance_tier == GovernanceTier.HUMAN_REVIEW:
        # Pause for human approval
        session_store.add_event(session_id, {
            "type": "human_approval_required",
            "action": proposed_action,
            "context": {
                "intent": detected_intent,
                "confidence": confidence,
                "entities": entities
            }
        })
        agent_response = "I need to verify this with our team. One moment please."
        
        session_store.add_event(session_id, {
            "type": "agent_response",
            "text": agent_response,
            "reasoning": reasoning_result
        })
        
        session["conversation_history"].append({
            "role": "ai",
            "content": agent_response
        })
        return {"status": "pending_approval", "text": agent_response, "governance_tier": governance_tier}
    
    elif governance_tier == GovernanceTier.PRIORITY_FLOW:
        # Provide safety instructions, then escalate
        safety_response = "For your safety, please follow these instructions: "
        if business_type == "hvac":
            safety_response = "If you smell gas or suspect a leak, please evacuate immediately and call 911. Then I'll connect you with our emergency technician."
        elif business_type in ["medical", "dental"]:
            safety_response = "For urgent medical concerns, please call 911 or go to your nearest emergency room. I'm connecting you with our medical team now."
        elif business_type == "law_firm":
            safety_response = "This sounds time-sensitive. I'm connecting you with an attorney right away."
        
        session_store.add_event(session_id, {
            "type": "human_intervention_request",
            "reason": f"Priority flow triggered for {detected_intent}",
            "context": {
                "intent": detected_intent,
                "confidence": confidence,
                "risk": reasoning_result.get("escalation_risk"),
                "governance_tier": governance_tier
            }
        })
        
        agent_response = safety_response + " " + reasoning_result.get("suggested_response", "Let me help you.")
        
        session_store.add_event(session_id, {
            "type": "agent_response",
            "text": agent_response,
            "reasoning": reasoning_result
        })
        
        session["conversation_history"].append({
            "role": "ai",
            "content": agent_response
        })
        return {"status": "processed", "text": agent_response, "governance_tier": governance_tier}
    
    elif governance_tier == GovernanceTier.CONFIRM_BEFORE_EXECUTE:
        # Add confirmation request to response
        confirmation_prompt = f"Would you like me to proceed with {proposed_action.replace('_', ' ').lower()}? "
        agent_response = reasoning_result.get("suggested_response", "I'm here to help.")
        agent_response = confirmation_prompt + agent_response
        
        # Store that confirmation is pending
        if http_session:
            http_session["pending_confirmation"] = {
                "action": proposed_action,
                "entities": entities,
                "governance_tier": governance_tier
            }
    
    # ===== END GOVERNANCE ENGINE =====
    
    # Get agent response
    agent_response = reasoning_result.get("suggested_response", "I'm here to help you.")
    
    # Extract entities from reasoning
    entities = reasoning_result.get("entities", {})
    menu_item = entities.get("menu_item") or entities.get("service")
    selected_action = reasoning_result.get("selected_action", "")
    
    # Initialize confirmation tracking if not exists
    if http_session and "confirmed_info" not in http_session:
        http_session["confirmed_info"] = {"name": False, "phone": False}
    
    # Extract and store customer info from entities OR from message text directly
    extracted_name = entities.get("customer_name")
    extracted_phone = entities.get("customer_phone")
    
    # FALLBACK: Extract phone number directly from message if not in entities
    # This handles cases where Nova fails to extract the phone
    message_text = message.text if hasattr(message, 'text') else str(message)
    message_lower = message_text.lower()
    
    if not extracted_phone:
        # Try to extract phone number from message text
        import re
        # Match various phone formats: 1234567890, 123-456-7890, (123) 456-7890, etc.
        phone_patterns = [
            r'(?:phone|number|cell|mobile|call|reach)[\s:]*([+]?\d[\d\s\-\(\)]{8,})',
            r'\b(\d{3}[\s\-]?\d{3}[\s\-]?\d{4})\b',  # 10 digit US format
            r'\b(\d{10,11})\b',  # Plain digits
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                # Clean up the phone number
                extracted_phone = re.sub(r'[^\d]', '', match.group(1))
                if len(extracted_phone) >= 10:
                    print(f"[Voice API] Extracted phone from message: {extracted_phone}")
                    break
    
    # FALLBACK: Extract name from message if not in entities
    if not extracted_name:
        name_patterns = [
            r'(?:name is|i am|call me|this is|my name\'s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:name is|i am|call me|this is|my name\'s)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                extracted_name = match.group(1).title()
                print(f"[Voice API] Extracted name from message: {extracted_name}")
                break
    
    if extracted_name and http_session:
        http_session["customer_name"] = extracted_name
    if extracted_phone and http_session:
        http_session["customer_phone"] = extracted_phone
    
    # Check if we already have all required info - override AI response if needed
    # This prevents the AI from asking for info we already have OR asking for confirmation repeatedly
    if http_session:
        customer_name = http_session.get("customer_name")
        customer_phone = http_session.get("customer_phone")
        confirmed_info = http_session.get("confirmed_info", {"name": False, "phone": False})
        
        # Detect if customer is confirming their info
        confirmation_keywords = ["yes", "correct", "that's right", "that is correct", "right", "confirmed", "confirm"]
        is_confirming = any(kw in message_lower for kw in confirmation_keywords)
        
        # If customer is confirming, mark the info as confirmed
        if is_confirming:
            if "phone" in suggested.lower() or "number" in suggested.lower():
                confirmed_info["phone"] = True
                http_session["confirmed_info"] = confirmed_info
            if "name" in suggested.lower():
                confirmed_info["name"] = True
                http_session["confirmed_info"] = confirmed_info
        
        # If AI is asking for info we already have AND already confirmed, don't ask again
        if customer_name and customer_phone:
            suggested = reasoning_result.get("suggested_response", "")
            asking_for_info = any(phrase in suggested.lower() for phrase in [
                "your name", "phone number", "confirm your", "provide your"
            ])
            
            # Check if we're asking for something that's already confirmed
            asking_for_confirmed = False
            if "phone" in suggested.lower() or "number" in suggested.lower():
                if confirmed_info.get("phone", False):
                    asking_for_confirmed = True
            if "name" in suggested.lower():
                if confirmed_info.get("name", False):
                    asking_for_confirmed = True
            
            if asking_for_info and asking_for_confirmed:
                # Stop asking - info is already confirmed
                reasoning_result["suggested_response"] = f"Great, thank you {customer_name}! Let me proceed with your appointment."
                reasoning_result["selected_action"] = "COLLECT_INFO"
                print(f"[Voice API] Skipping confirmation - info already confirmed: {confirmed_info}")
    
    # Extract delivery method from entities or message (reuse message_lower)
    delivery_method = entities.get("delivery_method")
    if "pickup" in message_lower or "pick up" in message_lower or "pick it up" in message_lower:
        delivery_method = "pickup"
    elif "delivery" in message_lower or "deliver" in message_lower:
        delivery_method = "delivery"
    if delivery_method and http_session:
        http_session["delivery_method"] = delivery_method
    
    # Get quantity from entities
    quantity = entities.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        quantity = 1
    
    # Check if price was already mentioned in conversation history
    price_already_mentioned = http_session.get("price_mentioned", False) if http_session else False
    if not price_already_mentioned and http_session:
        # Check conversation history for price mentions
        for msg in http_session.get("conversation_history", []):
            if msg.get("role") == "ai" and "$" in msg.get("content", ""):
                price_already_mentioned = True
                http_session["price_mentioned"] = True
                break
    
    # Detect clarification phrases - customer is NOT adding items
    clarification_phrases = [
        "i just wanted", "i didn't say", "i meant", "what i meant",
        "i already", "already ordered", "don't add", "didn't want to add",
        "no i didn't", "that's not what", "i said i wanted", "clarify",
        "i was just saying", "just clarifying", "i meant to say"
    ]
    is_clarification = any(phrase in message_lower for phrase in clarification_phrases)
    
    # Handle post-order confirmation context
    # If customer thanks us after order, acknowledge properly
    gratitude_phrases = ["thank you", "thanks", "thank", "thx", "appreciate it"]
    is_gratitude = any(phrase in message_lower for phrase in gratitude_phrases)
    
    if is_gratitude and http_session and http_session.get("order_confirmed"):
        last_order = http_session.get("last_order_summary", {})
        if last_order:
            agent_response = f"You're welcome! Your order ({last_order.get('items', 'your items')}) will be ready for {last_order.get('delivery_method', 'pickup')}. Is there anything else I can help you with?"
            session_store.add_event(session_id, {
                "type": "agent_response",
                "text": agent_response,
                "reasoning": reasoning_result
            })
            session["conversation_history"].append({
                "role": "ai",
                "content": agent_response
            })
            return {"status": "processed", "text": agent_response}
    
    # If customer confirms they want pickup/delivery, store it and ask for contact info
    if delivery_method and http_session and http_session.get("order_items"):
        # Check if we need customer info
        if not http_session.get("customer_name") or not http_session.get("customer_phone"):
            agent_response = f"Great! We'll have it ready for {delivery_method}. May I have your name and phone number for the order?"
            session_store.add_event(session_id, {
                "type": "agent_response",
                "text": agent_response,
                "reasoning": reasoning_result
            })
            session["conversation_history"].append({
                "role": "ai",
                "content": agent_response
            })
            return {"status": "processed", "text": agent_response}
    
    # Handle PLACE_ORDER action - ONLY when explicitly triggered by the model
    # DO NOT auto-trigger based on "order" keyword in message (causes duplicates)
    if selected_action == "PLACE_ORDER" and not is_clarification:
        if menu_item and business_context.get("menu") and http_session:
            menu_lower = menu_item.lower()
            for item in business_context.get("menu", []):
                if menu_lower in item.get("name", "").lower() or item.get("name", "").lower() in menu_lower:
                    # Initialize order_items if needed
                    if "order_items" not in http_session:
                        http_session["order_items"] = []
                    
                    # Check if item already in order (avoid duplicates)
                    existing = next((i for i in http_session.get("order_items", []) if i["name"].lower() == item["name"].lower()), None)
                    if existing:
                        # Item already exists - don't add again, just acknowledge
                        agent_response = f"You already have {existing.get('quantity', 1)}x {item['name']} in your order. Your total is ${sum(i.get('price', 0) * i.get('quantity', 1) for i in http_session['order_items']):.2f}. Would you like to add more, or shall I confirm your order?"
                    else:
                        # Add new item
                        order_entry = {
                            "name": item["name"],
                            "price": item.get("price", 0),
                            "quantity": quantity,
                            "menu_item_id": item.get("id")
                        }
                        http_session["order_items"].append(order_entry)
                        
                        # Build response asking for delivery method
                        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in http_session.get("order_items", []))
                        agent_response = f"Got it! Added {quantity}x {item['name']} to your order. Your current total is ${total:.2f}. Would you like pickup or delivery?"
                    break
    
    # Handle clarification about existing order
    elif is_clarification and http_session and http_session.get("order_items"):
        # Customer is clarifying, not adding - acknowledge their existing order
        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in http_session.get("order_items", []))
        items_list = ", ".join([f"{i.get('quantity', 1)}x {i['name']}" for i in http_session["order_items"]])
        agent_response = f"I understand. You have: {items_list}. Your total is ${total:.2f}. Would you like pickup or delivery?"
    
    # Handle CONFIRM_ORDER action - validate and save order to database
    elif selected_action == "CONFIRM_ORDER":
        if http_session and http_session.get("order_items"):
            # Check for missing required info
            missing_info = []
            if not http_session.get("customer_name"):
                missing_info.append("name")
            if not http_session.get("customer_phone"):
                missing_info.append("phone number")
            
            # If missing info, ask for it instead of confirming
            if missing_info:
                total = sum(item.get("price", 0) * item.get("quantity", 1) for item in http_session["order_items"])
                items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in http_session["order_items"]])
                
                if len(missing_info) == 2:
                    agent_response = f"Almost there! For your order of {items_list} (${total:.2f}), I'll need your name and phone number."
                else:
                    agent_response = f"Almost there! What's your {missing_info[0]} for the order?"
            else:
                # All info collected - proceed with order
                total = sum(item.get("price", 0) * item.get("quantity", 1) for item in http_session["order_items"])
                items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in http_session["order_items"]])
                
                try:
                    order = Order(
                        business_id=business_id,
                        customer_name=http_session.get("customer_name"),
                        customer_phone=http_session.get("customer_phone"),
                        status="confirmed",
                        total_amount=total,
                        confirmed_at=datetime.utcnow()
                    )
                    db.add(order)
                    db.flush()
                    
                    for item in http_session["order_items"]:
                        order_item = OrderItem(
                            order_id=order.id,
                            menu_item_id=item.get("menu_item_id"),
                            item_name=item["name"],
                            quantity=item.get("quantity", 1),
                            unit_price=item.get("price", 0)
                        )
                        db.add(order_item)
                    
                    db.commit()
                    print(f"[Voice API HTTP] Order {order.id} created successfully for business {business_id}")
                    
                    # Store order summary for context (don't clear immediately)
                    delivery_text = f" for {http_session.get('delivery_method', 'pickup')}" if http_session.get("delivery_method") else " for pickup"
                    http_session["order_confirmed"] = True
                    http_session["last_order_summary"] = {
                        "items": items_list,
                        "total": total,
                        "order_id": order.id,
                        "delivery_method": http_session.get("delivery_method", "pickup")
                    }
                    # Clear order items but keep context
                    http_session["order_items"] = []
                    
                    agent_response = f"Perfect! I've confirmed your order: {items_list}. Your total is ${total:.2f}{delivery_text}. We'll have it ready for you. Thank you!"
                except Exception as e:
                    print(f"[Voice API HTTP] Failed to create order: {e}")
                    db.rollback()
                    agent_response = f"I'm sorry, there was an issue processing your order. Please try again."
        else:
            # Check if we just completed an order
            if http_session and http_session.get("order_confirmed") and http_session.get("last_order_summary"):
                last_order = http_session["last_order_summary"]
                agent_response = f"You're welcome! Your order ({last_order['items']}) will be ready for {last_order.get('delivery_method', 'pickup')}. Is there anything else I can help you with?"
            else:
                agent_response = "I don't see any items in your order yet. Would you like to add anything?"
    
    # Handle CREATE_ORDER action - similar to CONFIRM_ORDER
    elif selected_action == "CREATE_ORDER":
        if http_session and http_session.get("order_items"):
            total = sum(item.get("price", 0) * item.get("quantity", 1) for item in http_session["order_items"])
            items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in http_session["order_items"]])
            
            try:
                order = Order(
                    business_id=business_id,
                    customer_name=http_session.get("customer_name"),
                    customer_phone=http_session.get("customer_phone"),
                    status="confirmed",
                    total_amount=total,
                    confirmed_at=datetime.utcnow()
                )
                db.add(order)
                db.flush()
                
                for item in http_session["order_items"]:
                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=item.get("menu_item_id"),
                        item_name=item["name"],
                        quantity=item.get("quantity", 1),
                        unit_price=item.get("price", 0)
                    )
                    db.add(order_item)
                
                db.commit()
                print(f"[Voice API HTTP] Order {order.id} created successfully for business {business_id}")
                
                http_session["order_confirmed"] = True
                http_session["order_items"] = []
                agent_response = f"Got it! I'm placing your order now for {items_list}. Your total is ${total:.2f}. Thank you!"
            except Exception as e:
                print(f"[Voice API HTTP] Failed to create order: {e}")
                db.rollback()
                agent_response = f"I'm sorry, there was an issue processing your order."
        else:
            agent_response = "I don't have any items in your order. What would you like to get?"
    
    # Handle price mention - only if not already mentioned in this conversation
    elif menu_item and business_context.get("menu") and not price_already_mentioned:
        menu_lower = menu_item.lower()
        for item in business_context.get("menu", []):
            if menu_lower in item.get("name", "").lower() or item.get("name", "").lower() in menu_lower:
                if item.get("price"):
                    price_str = f"${item['price']:.2f}"
                    # Only add price if not already in response
                    if "$" not in agent_response and "price" not in agent_response.lower():
                        unit_text = f" {item.get('unit', 'per item')}" if item.get('unit') and item.get('unit') != 'per item' else ''
                        agent_response = f"Our {item['name']} is {price_str}{unit_text}. {agent_response}"
                    # Mark that price was mentioned
                    if http_session:
                        http_session["price_mentioned"] = True
                    break
    
    # Calculate total if customer asks about total cost
    if http_session and http_session.get("order_items"):
        if "total" in message_lower or "cost me" in message_lower or "how much" in message_lower:
            total = sum(item.get("price", 0) * item.get("quantity", 1) for item in http_session["order_items"])
            items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in http_session["order_items"]])
            agent_response = f"You ordered: {items_list}. Your total is ${total:.2f}."

    # Handle other smart actions
    if selected_action == "SEND_DIRECTIONS":
        address = business_context.get("address", "our location")
        landmark = entities.get("landmark", "")
        landmark_text = f" near {landmark}" if landmark else ""
        agent_response = f"We are located at {address}{landmark_text}. {agent_response}"
    elif selected_action == "PAYMENT_PROCESS":
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in http_session.get("order_items", [])) if http_session else 0
        if total > 0:
            agent_response = f"I've initiated a secure payment process for your total of ${total:.2f}. I'm sending a secure link to your phone now. {agent_response}"
        else:
            agent_response = f"I'd be happy to help with that payment. Could you please confirm what you'd like to pay for? {agent_response}"
    elif selected_action == "HUMAN_INTERVENTION":
        session_store.add_event(session_id, {
            "type": "human_intervention_request",
            "reason": reasoning_result.get("safety_reason", "Unknown safety trigger"),
            "context": {
                "intent": reasoning_result.get("intent"),
                "confidence": reasoning_result.get("confidence"),
                "risk": reasoning_result.get("escalation_risk")
            }
        })
    
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

    # --- Pending appointment confirmation (HTTP sessions) ---
    if http_session and http_session.get("pending_appointment"):
        confirm_kw = ["yes", "yeah", "yep", "sure", "please", "book", "confirm", "go ahead", "do it", "ok", "okay"]
        decline_kw = ["no", "nah", "cancel", "don't", "different", "other", "change", "another"]
        user_confirms = any(kw in message_lower for kw in confirm_kw) and not any(kw in message_lower for kw in decline_kw)
        user_declines = any(kw in message_lower for kw in decline_kw)

        if user_confirms:
            pending = http_session.pop("pending_appointment")
            try:
                from app.services.calendar_service import calendar_service
                from datetime import timedelta
                result = await calendar_service.check_and_book_appointment(
                    business_id=business_id,
                    start_time=pending["start_time"],
                    end_time=pending["end_time"],
                    customer_name=http_session.get("customer_name") or customer_name or "Unknown",
                    customer_phone=http_session.get("customer_phone") or customer_phone or "Unknown",
                    service=pending.get("service", "General Checkup"),
                    db=db,
                )
                if result["success"]:
                    date_fmt = pending["start_time"].strftime("%B %d")
                    time_fmt = pending["start_time"].strftime("%I:%M %p")
                    agent_response = f"Great! I've booked your appointment for {date_fmt} at {time_fmt}. We'll see you then!"
                    appointment_created = True
                    print(f"[Voice API] Created appointment {result['appointment'].id} from pending confirmation")
                else:
                    agent_response = f"I'm sorry, I couldn't book that appointment. {result.get('message', 'Please try a different time.')}"
            except Exception as e:
                print(f"[Voice API] Pending appointment booking error: {e}")
                agent_response = "I'm having trouble booking that appointment right now. Could you please try again?"
        elif user_declines:
            http_session.pop("pending_appointment", None)
            agent_response = "No problem! Would you like to check a different time?"

        # Update the event with the corrected response
        session_store.add_event(session_id, {
            "type": "agent_response",
            "text": agent_response,
            "reasoning": reasoning_result,
        })
        session["conversation_history"].append({
            "role": "ai",
            "content": agent_response,
        })
        return {"status": "processed", "text": agent_response}

    if selected_action == "CREATE_APPOINTMENT":
        date_str = entities.get("date") or entities.get("preferred_date")
        time_str = entities.get("time") or entities.get("preferred_time")
        service = entities.get("service") or entities.get("service_type")
        
        # Check if preferred_time contains combined date+time (e.g., "tomorrow at 2pm")
        if time_str and (not date_str or not time_str):
            # Try to parse time_str as combined datetime
            appointment_time = parse_natural_datetime(None, time_str)
            if appointment_time:
                # Successfully parsed combined string
                pass
            else:
                # Fall back to separate date/time parsing
                appointment_time = parse_natural_datetime(date_str, time_str)
        else:
            appointment_time = parse_natural_datetime(date_str, time_str)
        
        if appointment_time:
            try:
                # Use calendar service for conflict checking and booking
                from app.services.calendar_service import calendar_service
                from datetime import timedelta
                
                end_time = appointment_time + timedelta(hours=1)  # Default 1-hour appointment
                
                result = await calendar_service.check_and_book_appointment(
                    business_id=business_id,
                    start_time=appointment_time,
                    end_time=end_time,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    service=service or "General Checkup",
                    db=db
                )
                
                if result["success"]:
                    print(f"[Voice API] Created appointment {result['appointment'].id} for {customer_phone} at {appointment_time}")
                    if result.get("calendar_event"):
                        print(f"[Voice API] Synced to calendar: {result['calendar_event'].get('id')}")
                    appointment_created = True
                else:
                    # Conflict detected - update agent response
                    conflicts = result.get("conflicts", [])
                    print(f"[Voice API] Appointment conflict: {conflicts}")
                    # Add conflict info to response
                    agent_response = f"I'm sorry, that time slot is not available. {agent_response}"
            except Exception as e:
                print(f"[Voice API] Failed to create appointment: {e}")
        else:
            # Couldn't parse date - ask for clarification
            print(f"[Voice API] Could not parse date/time: date='{date_str}', time='{time_str}'")
    
    # Also check if AI response mentions scheduling (fallback) - but only if we have a time
    # OR if customer asked about availability with a specific time (e.g., "is the doctor available at 2pm tomorrow?")
    availability_message = None
    if not appointment_created and ("scheduled" in agent_response.lower() or "booked" in agent_response.lower() or "available" in agent_response.lower() or "available at" in message_lower):
        # Try to extract date/time from the response or entities
        date_str = entities.get("date") or entities.get("preferred_date")
        time_str = entities.get("time") or entities.get("preferred_time")
        
        # Check if preferred_time contains both date and time (e.g., "tomorrow at 2pm")
        if time_str and (not date_str or not time_str):
            # Try to parse preferred_time as combined datetime
            appointment_time = parse_natural_datetime(None, time_str)
        else:
            appointment_time = parse_natural_datetime(date_str, time_str)
        
        if appointment_time:
            try:
                from app.services.calendar_service import calendar_service
                from datetime import timedelta
                
                end_time = appointment_time + timedelta(hours=1)
                
                # First check availability only
                integration = db.query(CalendarIntegration).filter(
                    CalendarIntegration.business_id == business_id,
                    CalendarIntegration.status == "active"
                ).first()
                
                if integration:
                    availability = await calendar_service.check_availability(integration, appointment_time, end_time, db)
                    is_available = availability.get("available", False)
                    
                    if not is_available:
                        # Not available - inform customer
                        date_str = appointment_time.strftime("%B %d")
                        time_str = appointment_time.strftime("%I:%M %p")
                        agent_response = f"I'm sorry, but {date_str} at {time_str} is not available. {availability.get('message', 'Please try a different time.')}"
                    else:
                        # Available - can we book it?
                        if "available at" in message_lower or "will.*available" in message_lower:
                            # Customer is asking about availability, not booking yet
                            date_str = appointment_time.strftime("%B %d")
                            time_str = appointment_time.strftime("%I:%M %p")
                            agent_response = f"Yes, {date_str} at {time_str} is available! Would you like me to book your appointment for that time?"
                            if http_session:
                                http_session["pending_appointment"] = {
                                    "start_time": appointment_time,
                                    "end_time": end_time,
                                    "service": entities.get("service") or entities.get("service_type") or "General Checkup",
                                }
                        else:
                            # Customer wants to book - proceed with booking
                            result = await calendar_service.check_and_book_appointment(
                                business_id=business_id,
                                start_time=appointment_time,
                                end_time=end_time,
                                customer_name=customer_name,
                                customer_phone=customer_phone,
                                service=entities.get("service") or entities.get("service_type") or "General Checkup",
                                db=db
                            )
                            
                            if result["success"]:
                                print(f"[Voice API] Created appointment from availability check at {appointment_time}")
                                appointment_created = True
                                date_str = appointment_time.strftime("%B %d")
                                time_str = appointment_time.strftime("%I:%M %p")
                                agent_response = f"Great! I've booked your appointment for {date_str} at {time_str}. {agent_response}"
                else:
                    # No calendar integration - check local DB conflicts
                    from app.models.models import Appointment
                    db_conflicts = calendar_service.check_db_conflicts(business_id, appointment_time, end_time, db)
                    
                    if db_conflicts:
                        date_str = appointment_time.strftime("%B %d")
                        time_str = appointment_time.strftime("%I:%M %p")
                        agent_response = f"I'm sorry, but {date_str} at {time_str} is already booked. Would you like to try a different time?"
                    else:
                        # Available locally
                        if "available at" in message_lower or "will.*available" in message_lower:
                            date_str = appointment_time.strftime("%B %d")
                            time_str = appointment_time.strftime("%I:%M %p")
                            agent_response = f"Yes, {date_str} at {time_str} is available! Would you like me to book your appointment for that time?"
                            if http_session:
                                http_session["pending_appointment"] = {
                                    "start_time": appointment_time,
                                    "end_time": end_time,
                                    "service": entities.get("service") or entities.get("service_type") or "General Checkup",
                                }
                        else:
                            # Book it
                            result = await calendar_service.check_and_book_appointment(
                                business_id=business_id,
                                start_time=appointment_time,
                                end_time=end_time,
                                customer_name=customer_name,
                                customer_phone=customer_phone,
                                service=entities.get("service") or entities.get("service_type") or "General Checkup",
                                db=db
                            )
                            
                            if result["success"]:
                                print(f"[Voice API] Created appointment from AI confirmation at {appointment_time}")
                                appointment_created = True
                                date_str = appointment_time.strftime("%B %d")
                                time_str = appointment_time.strftime("%I:%M %p")
                                agent_response = f"Great! I've booked your appointment for {date_str} at {time_str}. {agent_response}"
            except Exception as e:
                print(f"[Voice API] Failed to check availability or create appointment: {e}")
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