"""
Dashboard WebSocket endpoint for real-time updates and supervisor controls.
"""
import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.services.event_bus import event_bus, session_registry
from app.core.logging import get_logger

logger = get_logger("dashboard_ws")

router = APIRouter()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    business_id: int = Query(..., description="Business ID to monitor"),
):
    """
    WebSocket endpoint for dashboard real-time updates.

    Events received by dashboard:
    - call_start: New call started
    - call_end: Call ended
    - transcript: Live transcription update
    - ai_response: AI text response chunk
    - tool_execution: Tool was called
    - session_update: Session state changed

    Commands from dashboard (supervisor):
    - whisper: Send whisper message to AI (caller can't hear)
    - barge_in: Inject audio/text directly to caller
    - end_call: Force end a call
    """
    await websocket.accept()
    subscriber_id = f"dashboard-{business_id}-{uuid.uuid4().hex[:8]}"

    # Subscribe to event bus
    queue = event_bus.subscribe(subscriber_id)

    # Send initial state
    active_sessions = session_registry.get_all_sessions()
    business_sessions = {
        sid: {k: v for k, v in data.items() if k != "sonic_session"}
        for sid, data in active_sessions.items()
        if data.get("business_id") == business_id
    }

    await websocket.send_json({
        "type": "initial_state",
        "active_sessions": business_sessions,
        "subscriber_id": subscriber_id,
    })

    logger.info(f"Dashboard connected: {subscriber_id} for business {business_id}")

    # Two concurrent tasks: send events + receive commands
    async def send_events():
        """Forward events from event_bus to WebSocket."""
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                # Filter events for this business
                if event.get("business_id") == business_id or event.get("business_id") is None:
                    await websocket.send_json(event)
        except Exception as e:
            logger.debug(f"Send events ended: {e}")

    async def receive_commands():
        """Receive supervisor commands from dashboard."""
        try:
            while True:
                data = await websocket.receive_json()
                command = data.get("command")
                session_id = data.get("session_id")

                if command == "whisper":
                    # Whisper: inject text into AI's system prompt
                    text = data.get("text", "")
                    session_data = session_registry.get_session(session_id)
                    if session_data and session_data.get("sonic_session"):
                        sonic = session_data["sonic_session"]
                        whisper_directive = f"\n\n[SUPERVISOR WHISPER]: {text}"
                        sonic.system_prompt += whisper_directive
                        logger.info(f"Whisper injected to session {session_id}: {text[:50]}")
                        await websocket.send_json({
                            "type": "command_ack",
                            "command": "whisper",
                            "session_id": session_id,
                            "success": True,
                        })
                    else:
                        await websocket.send_json({
                            "type": "command_ack",
                            "command": "whisper",
                            "session_id": session_id,
                            "success": False,
                            "error": "Session not found",
                        })

                elif command == "barge_in":
                    # Barge-in: synthesize text and inject into caller's audio stream
                    text = data.get("text", "")
                    session_data = session_registry.get_session(session_id)
                    if session_data and session_data.get("sonic_session"):
                        sonic = session_data["sonic_session"]
                        # Synthesize the supervisor text
                        try:
                            from app.services.nova_sonic import nova_sonic
                            audio_data = await nova_sonic._synthesize_speech(text)
                            if audio_data:
                                audio_b64 = nova_sonic.encode_audio_base64(audio_data)
                                await sonic.audio_queue.put({
                                    "audio": audio_b64,
                                    "sample_rate": 16000,
                                    "is_barge_in": True,
                                })
                                logger.info(f"Barge-in sent to session {session_id}")
                        except Exception as e:
                            logger.error(f"Barge-in TTS failed: {e}")

                        await websocket.send_json({
                            "type": "command_ack",
                            "command": "barge_in",
                            "session_id": session_id,
                            "success": True,
                        })
                    else:
                        await websocket.send_json({
                            "type": "command_ack",
                            "command": "barge_in",
                            "session_id": session_id,
                            "success": False,
                            "error": "Session not found",
                        })

                elif command == "end_call":
                    session_data = session_registry.get_session(session_id)
                    if session_data and session_data.get("sonic_session"):
                        sonic = session_data["sonic_session"]
                        await sonic.close()
                        logger.info(f"Force-ended session {session_id}")
                        await websocket.send_json({
                            "type": "command_ack",
                            "command": "end_call",
                            "session_id": session_id,
                            "success": True,
                        })
                    else:
                        await websocket.send_json({
                            "type": "command_ack",
                            "command": "end_call",
                            "session_id": session_id,
                            "success": False,
                            "error": "Session not found",
                        })

                elif command == "get_active_sessions":
                    sessions = session_registry.get_all_sessions()
                    business_sessions = {
                        sid: {k: v for k, v in d.items() if k != "sonic_session"}
                        for sid, d in sessions.items()
                        if d.get("business_id") == business_id
                    }
                    await websocket.send_json({
                        "type": "active_sessions",
                        "sessions": business_sessions,
                    })

        except WebSocketDisconnect:
            logger.debug(f"Dashboard disconnected: {subscriber_id}")
        except Exception as e:
            logger.debug(f"Receive commands ended: {e}")

    try:
        # Run both tasks concurrently
        send_task = asyncio.create_task(send_events())
        receive_task = asyncio.create_task(receive_commands())

        done, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        logger.info(f"Dashboard disconnected: {subscriber_id}")
    except Exception as e:
        logger.error(f"Dashboard WS error: {e}")
    finally:
        event_bus.unsubscribe(subscriber_id)
        logger.info(f"Dashboard cleaned up: {subscriber_id}")
