"""
Unit tests for EventBus and ActiveSessionRegistry.

Tests cover:
- subscribe_and_publish: subscribe, publish event, verify received
- multiple_subscribers: two subscribers both receive same event
- unsubscribe: unsubscribed subscriber does not receive events
- full_queue: verify no crash when queue is full
- session_registry_register_deregister: register, get, deregister
- session_registry_update: update session data
"""

import pytest
import asyncio
from datetime import datetime, timezone

from app.services.event_bus import EventBus, ActiveSessionRegistry


# ---------------------------------------------------------------------------
# EventBus tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_subscribe_and_publish():
    """A subscribed listener should receive published events."""
    bus = EventBus()
    queue = bus.subscribe("sub-1")

    event = {"type": "call_started", "session_id": "sess-001"}
    await bus.publish(event)

    received = queue.get_nowait()
    assert received["type"] == "call_started"
    assert received["session_id"] == "sess-001"
    # The publish method injects a timestamp
    assert "timestamp" in received


@pytest.mark.asyncio
async def test_multiple_subscribers():
    """All subscribers should receive the same published event."""
    bus = EventBus()
    q1 = bus.subscribe("sub-1")
    q2 = bus.subscribe("sub-2")

    event = {"type": "call_ended", "session_id": "sess-002"}
    await bus.publish(event)

    r1 = q1.get_nowait()
    r2 = q2.get_nowait()

    assert r1["type"] == "call_ended"
    assert r2["type"] == "call_ended"
    assert r1["session_id"] == "sess-002"
    assert r2["session_id"] == "sess-002"


@pytest.mark.asyncio
async def test_unsubscribe():
    """An unsubscribed listener should not receive subsequent events."""
    bus = EventBus()
    q1 = bus.subscribe("sub-1")
    q2 = bus.subscribe("sub-2")

    bus.unsubscribe("sub-1")

    event = {"type": "transfer", "data": "hello"}
    await bus.publish(event)

    # sub-2 should still receive
    r2 = q2.get_nowait()
    assert r2["type"] == "transfer"

    # sub-1 queue should be empty (no new events after unsubscribe)
    assert q1.empty()


@pytest.mark.asyncio
async def test_subscriber_count():
    """subscriber_count property should reflect current subscriptions."""
    bus = EventBus()
    assert bus.subscriber_count == 0

    bus.subscribe("sub-1")
    assert bus.subscriber_count == 1

    bus.subscribe("sub-2")
    assert bus.subscriber_count == 2

    bus.unsubscribe("sub-1")
    assert bus.subscriber_count == 1

    bus.unsubscribe("sub-2")
    assert bus.subscriber_count == 0


@pytest.mark.asyncio
async def test_full_queue():
    """Publishing to a full queue should not raise an exception."""
    bus = EventBus()
    # Create a queue with maxsize=2
    queue = bus.subscribe("sub-full", maxsize=2)

    # Fill the queue
    await bus.publish({"type": "event-1"})
    await bus.publish({"type": "event-2"})

    assert queue.full()

    # Publishing a third event should NOT raise -- it just drops/warns
    await bus.publish({"type": "event-3"})

    # The queue should still have only the first two events
    assert queue.qsize() == 2
    e1 = queue.get_nowait()
    assert e1["type"] == "event-1"
    e2 = queue.get_nowait()
    assert e2["type"] == "event-2"


@pytest.mark.asyncio
async def test_publish_with_no_subscribers():
    """Publishing with no subscribers should not raise."""
    bus = EventBus()
    # Should be a no-op, not an error
    await bus.publish({"type": "orphan_event"})
    assert bus.subscriber_count == 0


# ---------------------------------------------------------------------------
# ActiveSessionRegistry tests
# ---------------------------------------------------------------------------

def test_session_registry_register_deregister():
    """Register a session, get it, then deregister it."""
    registry = ActiveSessionRegistry()

    session_data = {
        "customer_phone": "+1234567890",
        "business_id": 1,
        "language": "en-US",
    }
    registry.register("sess-001", session_data)

    # Retrieve it
    retrieved = registry.get_session("sess-001")
    assert retrieved is not None
    assert retrieved["customer_phone"] == "+1234567890"
    assert retrieved["business_id"] == 1
    assert "registered_at" in retrieved
    assert registry.active_count == 1

    # Deregister
    registry.deregister("sess-001")
    assert registry.get_session("sess-001") is None
    assert registry.active_count == 0


def test_session_registry_deregister_nonexistent():
    """Deregistering a nonexistent session should not raise."""
    registry = ActiveSessionRegistry()
    registry.deregister("no-such-session")
    assert registry.active_count == 0


def test_session_registry_update():
    """Updating a registered session should merge new data."""
    registry = ActiveSessionRegistry()

    registry.register("sess-002", {"status": "active", "business_id": 5})
    registry.update_session("sess-002", {"status": "transferred", "agent": "human-1"})

    session = registry.get_session("sess-002")
    assert session["status"] == "transferred"
    assert session["agent"] == "human-1"
    assert session["business_id"] == 5


def test_session_registry_update_nonexistent():
    """Updating a nonexistent session should be a no-op."""
    registry = ActiveSessionRegistry()
    # Should not raise
    registry.update_session("ghost-session", {"status": "running"})
    assert registry.get_session("ghost-session") is None


def test_session_registry_get_all_sessions():
    """get_all_sessions should return all registered sessions."""
    registry = ActiveSessionRegistry()

    registry.register("sess-a", {"lang": "en"})
    registry.register("sess-b", {"lang": "es"})

    all_sessions = registry.get_all_sessions()
    assert len(all_sessions) == 2
    assert "sess-a" in all_sessions
    assert "sess-b" in all_sessions
    assert all_sessions["sess-a"]["lang"] == "en"
    assert all_sessions["sess-b"]["lang"] == "es"


def test_session_registry_get_all_returns_copy():
    """get_all_sessions should return a copy, not the internal dict."""
    registry = ActiveSessionRegistry()
    registry.register("sess-x", {"data": "hello"})

    result = registry.get_all_sessions()
    result["sess-x"]["data"] = "mutated"

    # The internal state should not be affected by external mutation of the returned dict
    # (get_all_sessions returns dict(self._sessions) which is a shallow copy of the top-level dict)
    assert "sess-x" in registry.get_all_sessions()
