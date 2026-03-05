"""
Event Bus - In-process pub/sub for real-time dashboard updates.
Provides fan-out to multiple WebSocket subscribers and active session tracking.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Set
from datetime import datetime, timezone
from app.core.logging import get_logger

logger = get_logger("event_bus")


class EventBus:
    """
    In-process event bus with asyncio.Queue fan-out per subscriber.
    Subscribers receive copies of all published events.
    """

    def __init__(self):
        self._subscribers: Dict[str, asyncio.Queue] = {}

    def subscribe(self, subscriber_id: str, maxsize: int = 200) -> asyncio.Queue:
        """Subscribe and get a queue to receive events."""
        queue = asyncio.Queue(maxsize=maxsize)
        self._subscribers[subscriber_id] = queue
        logger.info(f"Subscriber {subscriber_id} added. Total: {len(self._subscribers)}")
        return queue

    def unsubscribe(self, subscriber_id: str):
        """Remove a subscriber."""
        self._subscribers.pop(subscriber_id, None)
        logger.info(f"Subscriber {subscriber_id} removed. Total: {len(self._subscribers)}")

    async def publish(self, event: Dict[str, Any]):
        """Publish event to all subscribers (fan-out)."""
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        dead = []
        for sub_id, queue in self._subscribers.items():
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for subscriber {sub_id}, dropping event")
                dead.append(sub_id)
        for sub_id in dead:
            # Don't remove on full - just warn. Dashboard will reconnect if needed.
            pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


class ActiveSessionRegistry:
    """
    Tracks active call sessions for supervisor controls (whisper/barge-in).
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def register(self, session_id: str, session_data: Dict[str, Any]):
        """Register an active session."""
        self._sessions[session_id] = {
            **session_data,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"Session {session_id} registered. Active: {len(self._sessions)}")

    def deregister(self, session_id: str):
        """Remove a session."""
        self._sessions.pop(session_id, None)
        logger.info(f"Session {session_id} deregistered. Active: {len(self._sessions)}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions."""
        return dict(self._sessions)

    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data."""
        if session_id in self._sessions:
            self._sessions[session_id].update(updates)

    @property
    def active_count(self) -> int:
        return len(self._sessions)


# Module-level singletons
event_bus = EventBus()
session_registry = ActiveSessionRegistry()
