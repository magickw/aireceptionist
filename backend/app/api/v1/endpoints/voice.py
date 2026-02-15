"""
Voice WebSocket Endpoint
Handles real-time voice communication with Nova 2 Sonic and reasoning
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any, AsyncGenerator, Optional
import json
import asyncio
import base64
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from app.services.nova_reasoning import nova_reasoning
from app.services.nova_sonic import nova_sonic, AudioBuffer, LatencyTracker
from app.api.deps import get_current_business_id, get_current_active_user, get_db
from app.models.models import User, Appointment, Order, OrderItem, MenuItem, CallSession
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
    # Track session state (like order items) for the duration of the WebSocket
    ws_session = {
        "order_items": [],
        "created_at": datetime.utcnow(),
        "business_id": business_id,
        "customer_name": None,
        "customer_phone": None
    }
    
    try:
        await manager.connect(websocket, session_id)
        
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
                
                # Store customer info from entities if extracted
                if entities.get("customer_name"):
                    ws_session["customer_name"] = entities.get("customer_name")
                if entities.get("customer_phone"):
                    ws_session["customer_phone"] = entities.get("customer_phone")
                
                # Handle specific actions from reasoning
                selected_action = reasoning_result.get("selected_action")
                menu_item = entities.get("menu_item") or entities.get("service")
                quantity = entities.get("quantity", 1) if isinstance(entities.get("quantity"), int) else 1
                
                # Detect if this is an order request based on intent or action
                intent = reasoning_result.get("intent", "").lower()
                is_order_intent = selected_action == "PLACE_ORDER" or "order" in intent or "place_order" in intent
                
                # Handle PLACE_ORDER action or detected order intent
                if selected_action == "PLACE_ORDER" or (is_order_intent and menu_item):
                    if menu_item and business_context.get("menu"):
                        menu_lower = menu_item.lower()
                        for item in business_context.get("menu", []):
                            if menu_lower in item.get("name", "").lower() or item.get("name", "").lower() in menu_lower:
                                # Check if item already in order (avoid duplicates)
                                existing = next((i for i in ws_session["order_items"] if i["name"] == item["name"]), None)
                                if existing:
                                    existing["quantity"] = existing.get("quantity", 1) + quantity
                                else:
                                    order_entry = {
                                        "name": item["name"],
                                        "price": item.get("price", 0),
                                        "quantity": quantity,
                                        "menu_item_id": item.get("id")
                                    }
                                    ws_session["order_items"].append(order_entry)
                                
                                # Build confirmation response
                                total = sum(i.get("price", 0) * i.get("quantity", 1) for i in ws_session["order_items"])
                                agent_response = f"Got it! Added {quantity}x {item['name']} to your order. Your current total is ${total:.2f}. Would you like to add anything else, or shall I confirm your order?"
                                break
                
                elif selected_action == "CONFIRM_ORDER":
                    # Save the order to the database
                    if ws_session["order_items"]:
                        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in ws_session["order_items"])
                        items_list = ", ".join([f"{item.get('quantity', 1)}x {item['name']}" for item in ws_session["order_items"]])
                        agent_response = f"Perfect! I've confirmed your order: {items_list}. Your total is ${total:.2f}. Your order has been placed and will be ready shortly. Thank you!"
                        
                        # Store order info for later database persistence
                        ws_session["order_confirmed"] = True
                        ws_session["order_total"] = total
                    else:
                        agent_response = f"I don't see any items in your order yet. Would you like to order something?"
                
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
                # End the call - save session and order
                summary = " | ".join([f"{m['role']}: {m['content'][:100]}" for m in conversation_history[-5:]]) if conversation_history else ""
                _end_call_session(ws_session, session_id, summary, final_sentiment)
                await _save_confirmed_order(ws_session, session_id)
                await manager.send_json(session_id, {
                    "type": "call_ended",
                    "message": "Call ended"
                })
                break
    
    except WebSocketDisconnect:
        # Save session and any confirmed orders before disconnecting
        summary = " | ".join([f"{m['role']}: {m['content'][:100]}" for m in conversation_history[-5:]]) if 'conversation_history' in dir() and conversation_history else ""
        _end_call_session(ws_session, session_id, summary, final_sentiment if 'final_sentiment' in dir() else "neutral")
        await _save_confirmed_order(ws_session, session_id)
        manager.disconnect(session_id)
    except Exception as e:
        await manager.send_json(session_id, {
            "type": "error",
            "message": f"Error: {str(e)}"
        })
        # Try to save session and order even on error
        summary = " | ".join([f"{m['role']}: {m['content'][:100]}" for m in conversation_history[-5:]]) if 'conversation_history' in dir() and conversation_history else ""
        _end_call_session(ws_session, session_id, summary, final_sentiment if 'final_sentiment' in dir() else "neutral")
        await _save_confirmed_order(ws_session, session_id)
        manager.disconnect(session_id)


async def _save_confirmed_order(ws_session: Dict[str, Any], session_id: str) -> None:
    """Save a confirmed order to the database."""
    if not ws_session.get("order_confirmed") or not ws_session.get("order_items"):
        return
    
    try:
        from app.api.deps import get_db
        gen = get_db()
        db = next(gen)
        
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
    except Exception as e:
        print(f"Failed to save order: {e}")
    finally:
        try:
            db.close()
        except:
            pass


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
            "order_items": [],  # Track items ordered
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
    
    # Enhance response with actual pricing if customer asked about menu item
    entities = reasoning_result.get("entities", {})
    menu_item = entities.get("menu_item") or entities.get("service")
    
    # If customer asked about pricing and we have menu info, include actual price
    order_items = []
    if menu_item and business_context.get("menu"):
        menu_lower = menu_item.lower()
        for item in business_context.get("menu", []):
            if menu_lower in item.get("name", "").lower() or item.get("name", "").lower() in menu_lower:
                if item.get("price"):
                    price_str = f"${item['price']:.2f}"
                    order_items.append({"name": item["name"], "price": item["price"]})
                    # Include price only once
                    if "Our" not in agent_response:
                        unit_text = f" {item.get('unit', 'per item')}" if item.get('unit') and item.get('unit') != 'per item' else ''
                        agent_response = f"Our {item['name']} is {price_str}{unit_text}. {agent_response}"
                    break
    
    # Track order items in session
    http_session = session_store.get_session(session_id)
    if order_items and http_session:
        if "order_items" not in http_session:
            http_session["order_items"] = []
        http_session["order_items"].extend(order_items)
    
    # Calculate total if customer asks about total cost
    if message:
        message_lower = message.text.lower() if hasattr(message, 'text') else str(message).lower()
        if http_session and "order_items" in http_session and http_session["order_items"]:
            if "total" in message_lower or "cost me" in message_lower or "how much" in message_lower:
                total = sum(item["price"] for item in http_session["order_items"])
                items_list = ", ".join([item["name"] for item in http_session["order_items"]])
                if len(http_session["order_items"]) > 1:
                    agent_response = f"You ordered: {items_list}. Your total is ${total:.2f}. {agent_response}"

    # Handle specific smart actions
    selected_action = reasoning_result.get("selected_action", "")
    if selected_action == "SEND_DIRECTIONS":
        address = business_context.get("address", "our location")
        landmark = entities.get("landmark", "")
        landmark_text = f" near {landmark}" if landmark else ""
        agent_response = f"We are located at {address}{landmark_text}. {agent_response}"
    elif selected_action == "PAYMENT_PROCESS":
        total = sum(item["price"] for item in http_session["order_items"]) if http_session and "order_items" in http_session else 0
        if total > 0:
            agent_response = f"I've initiated a secure payment process for your total of ${total:.2f}. I'm sending a secure link to your phone now. {agent_response}"
        else:
            agent_response = f"I'd be happy to help with that payment. Could you please confirm what you'd like to pay for? {agent_response}"
    elif selected_action == "HUMAN_INTERVENTION":
        # Add intervention request event
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
    
    if selected_action == "CREATE_APPOINTMENT":
        date_str = entities.get("date")
        time_str = entities.get("time")
        service = entities.get("service")
        
        # Use the natural language date parser
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
    if not appointment_created and ("scheduled" in agent_response.lower() or "booked" in agent_response.lower()):
        # Try to extract date/time from the response or entities
        date_str = entities.get("date")
        time_str = entities.get("time")
        appointment_time = parse_natural_datetime(date_str, time_str)
        
        if appointment_time:
            try:
                from app.services.calendar_service import calendar_service
                from datetime import timedelta
                
                end_time = appointment_time + timedelta(hours=1)
                
                result = await calendar_service.check_and_book_appointment(
                    business_id=business_id,
                    start_time=appointment_time,
                    end_time=end_time,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    service=entities.get("service", "Checkup"),
                    db=db
                )
                
                if result["success"]:
                    print(f"[Voice API] Created appointment from AI confirmation at {appointment_time}")
            except Exception as e:
                print(f"[Voice API] Failed to create appointment: {e}")
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