"""
Unit tests for CustomerMemoryService.

Tests cover:
- save_memory (new creation)
- save_memory (upsert behavior)
- get_memories (filtered by type)
- build_memory_briefing (natural-language summary format)
- recall_customer_memory (keyword search)
- summarize_call (LLM-powered summarization via mocked Bedrock)
"""

import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone

from app.services.customer_memory_service import CustomerMemoryService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_memory_mock(
    id=1,
    customer_id=10,
    business_id=1,
    memory_type="preference",
    key="preferred_time",
    value="mornings",
    confidence=0.95,
    access_count=0,
    source_session_id=None,
    created_at=None,
    updated_at=None,
):
    """Return a MagicMock that behaves like a CustomerMemory ORM instance."""
    mem = MagicMock()
    mem.id = id
    mem.customer_id = customer_id
    mem.business_id = business_id
    mem.memory_type = memory_type
    mem.key = key
    mem.value = value
    mem.confidence = confidence
    mem.access_count = access_count
    mem.source_session_id = source_session_id
    mem.created_at = created_at or datetime(2026, 3, 1, tzinfo=timezone.utc)
    mem.updated_at = updated_at or datetime(2026, 3, 1, tzinfo=timezone.utc)
    return mem


def _make_call_summary_mock(summary="Called about appointment", customer_id=10, business_id=1):
    """Return a MagicMock that behaves like a CallSummaryV2 ORM instance."""
    cs = MagicMock()
    cs.summary = summary
    cs.customer_id = customer_id
    cs.business_id = business_id
    cs.created_at = datetime(2026, 3, 1, tzinfo=timezone.utc)
    return cs


@pytest.fixture
def service():
    return CustomerMemoryService()


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    db.rollback = MagicMock()
    return db


# ---------------------------------------------------------------------------
# test_save_memory_creates_new
# ---------------------------------------------------------------------------

def test_save_memory_creates_new(service, mock_db):
    """Saving a memory that does not exist should create a new row."""

    # query(...).filter(...).first() returns None => new memory
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # When db.refresh is called, simulate assigning an id to the memory object
    def fake_refresh(obj):
        obj.id = 42

    mock_db.refresh.side_effect = fake_refresh

    with patch("app.services.customer_memory_service.CustomerMemory") as MockModel:
        instance = _make_memory_mock(id=None, key="preferred_time", value="mornings")
        MockModel.return_value = instance
        MockModel.customer_id = MagicMock()
        MockModel.key = MagicMock()

        result = service.save_memory(
            db=mock_db,
            customer_id=10,
            business_id=1,
            memory_type="preference",
            key="preferred_time",
            value="mornings",
            confidence=0.95,
        )

    # The db.add should have been called once for the new row
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called()
    assert result["key"] == "preferred_time"
    assert result["value"] == "mornings"
    assert result["memory_type"] == "preference"


# ---------------------------------------------------------------------------
# test_save_memory_upserts
# ---------------------------------------------------------------------------

def test_save_memory_upserts(service, mock_db):
    """Saving a memory with the same key should update, not duplicate."""

    existing = _make_memory_mock(
        id=5, key="preferred_time", value="afternoons", memory_type="preference"
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing

    result = service.save_memory(
        db=mock_db,
        customer_id=10,
        business_id=1,
        memory_type="preference",
        key="preferred_time",
        value="mornings",
        confidence=1.0,
    )

    # The existing object's value should be updated
    assert existing.value == "mornings"
    # db.add should NOT be called because we are updating an existing row
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called()
    assert result["value"] == "mornings"


# ---------------------------------------------------------------------------
# test_get_memories
# ---------------------------------------------------------------------------

def test_get_memories(service, mock_db):
    """get_memories should return memories filtered by type and increment access_count."""

    mem1 = _make_memory_mock(id=1, memory_type="preference", key="time", value="AM")
    mem2 = _make_memory_mock(id=2, memory_type="preference", key="day", value="Monday")

    # Simulate the chained query builder
    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = [mem1, mem2]

    results = service.get_memories(
        db=mock_db,
        customer_id=10,
        business_id=1,
        memory_type="preference",
    )

    assert len(results) == 2
    assert results[0]["key"] == "time"
    assert results[1]["key"] == "day"

    # access_count should have been incremented
    assert mem1.access_count == 1
    assert mem2.access_count == 1
    mock_db.commit.assert_called()


# ---------------------------------------------------------------------------
# test_build_memory_briefing
# ---------------------------------------------------------------------------

def test_build_memory_briefing(service, mock_db):
    """build_memory_briefing should produce a formatted briefing string."""

    pref_mem = _make_memory_mock(
        id=1, memory_type="preference", key="Preferred appointment time", value="mornings"
    )
    fact_mem = _make_memory_mock(
        id=2, memory_type="fact", key="pet_count", value="Has 2 dogs"
    )

    call_summary = _make_call_summary_mock(summary="Booked grooming appointment, was satisfied")

    # First query (CustomerMemory) returns memories
    memory_query = MagicMock()
    memory_query.filter.return_value = memory_query
    memory_query.order_by.return_value = memory_query
    memory_query.limit.return_value = memory_query
    memory_query.all.return_value = [pref_mem, fact_mem]

    # Second query (CallSummaryV2) returns a summary
    summary_query = MagicMock()
    summary_query.filter.return_value = summary_query
    summary_query.order_by.return_value = summary_query
    summary_query.first.return_value = call_summary

    # db.query is called twice: first for CustomerMemory, then for CallSummaryV2
    mock_db.query.side_effect = [memory_query, summary_query]

    briefing = service.build_memory_briefing(
        db=mock_db,
        customer_id=10,
        business_id=1,
    )

    assert "## Customer Memory Briefing" in briefing
    assert "[preference] Preferred appointment time: mornings" in briefing
    assert "[fact] Has 2 dogs" in briefing
    assert "Last call summary: Booked grooming appointment, was satisfied" in briefing


# ---------------------------------------------------------------------------
# test_build_memory_briefing_no_memories_with_summary
# ---------------------------------------------------------------------------

def test_build_memory_briefing_no_memories_with_summary(service, mock_db):
    """When no memories exist but a call summary does, briefing should include only summary."""

    call_summary = _make_call_summary_mock(summary="Quick billing inquiry resolved")

    # First query (CustomerMemory) returns empty
    memory_query = MagicMock()
    memory_query.filter.return_value = memory_query
    memory_query.order_by.return_value = memory_query
    memory_query.limit.return_value = memory_query
    memory_query.all.return_value = []

    # Second query (CallSummaryV2) returns a summary
    summary_query = MagicMock()
    summary_query.filter.return_value = summary_query
    summary_query.order_by.return_value = summary_query
    summary_query.first.return_value = call_summary

    mock_db.query.side_effect = [memory_query, summary_query]

    briefing = service.build_memory_briefing(db=mock_db, customer_id=10, business_id=1)

    assert "## Customer Memory Briefing" in briefing
    assert "Last call summary: Quick billing inquiry resolved" in briefing


# ---------------------------------------------------------------------------
# test_build_memory_briefing_empty
# ---------------------------------------------------------------------------

def test_build_memory_briefing_empty(service, mock_db):
    """When no memories and no call summary exist, briefing should be empty string."""

    memory_query = MagicMock()
    memory_query.filter.return_value = memory_query
    memory_query.order_by.return_value = memory_query
    memory_query.limit.return_value = memory_query
    memory_query.all.return_value = []

    summary_query = MagicMock()
    summary_query.filter.return_value = summary_query
    summary_query.order_by.return_value = summary_query
    summary_query.first.return_value = None

    mock_db.query.side_effect = [memory_query, summary_query]

    briefing = service.build_memory_briefing(db=mock_db, customer_id=10, business_id=1)

    assert briefing == ""


# ---------------------------------------------------------------------------
# test_recall_customer_memory
# ---------------------------------------------------------------------------

def test_recall_customer_memory(service, mock_db):
    """recall_customer_memory should return memories matching the query keyword."""

    matching_mem = _make_memory_mock(
        id=3, memory_type="fact", key="pet_count", value="2 dogs"
    )

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = [matching_mem]

    results = service.recall_customer_memory(
        db=mock_db,
        customer_id=10,
        business_id=1,
        query="dog",
    )

    assert len(results) == 1
    assert results[0]["value"] == "2 dogs"
    # access_count should be incremented
    assert matching_mem.access_count == 1


# ---------------------------------------------------------------------------
# test_recall_customer_memory_empty_query
# ---------------------------------------------------------------------------

def test_recall_customer_memory_empty_query(service, mock_db):
    """recall_customer_memory with empty query should return empty list."""

    results = service.recall_customer_memory(
        db=mock_db,
        customer_id=10,
        business_id=1,
        query="",
    )

    assert results == []
    mock_db.query.assert_not_called()


# ---------------------------------------------------------------------------
# test_summarize_call
# ---------------------------------------------------------------------------

@patch("app.services.customer_memory_service.boto3")
@patch("app.services.customer_memory_service.settings")
def test_summarize_call(mock_settings, mock_boto3, service, mock_db):
    """summarize_call should call Bedrock converse, persist summary, and extract facts."""

    mock_settings.AWS_REGION = "us-east-1"
    mock_settings.AWS_ACCESS_KEY_ID = "fake-key"
    mock_settings.AWS_SECRET_ACCESS_KEY = "fake-secret"

    # Mock Bedrock client and converse response
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    summary_json = {
        "summary": "Customer booked a grooming appointment for next Tuesday.",
        "key_topics": ["appointment", "grooming"],
        "outcome": "appointment_booked",
        "action_items": ["Confirm appointment by SMS"],
        "extracted_facts": {"preferred_time": "mornings", "pet_count": "2 dogs"},
        "sentiment_arc": "neutral->positive",
    }

    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [{"text": json.dumps(summary_json)}]
            }
        }
    }

    # Mock the query for CallSummaryV2 (used internally)
    with patch("app.services.customer_memory_service.CallSummaryV2") as MockSummaryModel:
        mock_summary_instance = MagicMock()
        mock_summary_instance.id = 99
        MockSummaryModel.return_value = mock_summary_instance

        # For save_memory calls on extracted facts, mock the CustomerMemory query
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.customer_memory_service.CustomerMemory") as MockMemModel:
            MockMemModel.return_value = _make_memory_mock()
            MockMemModel.customer_id = MagicMock()
            MockMemModel.key = MagicMock()

            result = service.summarize_call(
                db=mock_db,
                call_session_id="session-abc-123",
                customer_id=10,
                business_id=1,
                conversation_messages=[
                    {"sender": "customer", "content": "I'd like to book a grooming appointment."},
                    {"sender": "ai", "content": "Sure! When would you like to come in?"},
                    {"sender": "customer", "content": "Next Tuesday morning please."},
                ],
            )

    # Verify Bedrock was called
    mock_boto3.client.assert_called_once()
    mock_client.converse.assert_called_once()

    # Verify the response data
    assert result["summary"] == "Customer booked a grooming appointment for next Tuesday."
    assert result["key_topics"] == ["appointment", "grooming"]
    assert result["outcome"] == "appointment_booked"
    assert result["sentiment_arc"] == "neutral->positive"
    assert result["extracted_facts"]["preferred_time"] == "mornings"

    # Verify that CallSummaryV2 was persisted
    mock_db.add.assert_called()


# ---------------------------------------------------------------------------
# test_summarize_call_empty_messages
# ---------------------------------------------------------------------------

def test_summarize_call_empty_messages(service, mock_db):
    """summarize_call with no messages should return empty dict immediately."""

    result = service.summarize_call(
        db=mock_db,
        call_session_id="session-empty",
        customer_id=10,
        business_id=1,
        conversation_messages=[],
    )

    assert result == {}
    mock_db.add.assert_not_called()


# ---------------------------------------------------------------------------
# test_flush_session_memories
# ---------------------------------------------------------------------------

def test_flush_session_memories(service, mock_db):
    """flush_session_memories should batch-save multiple memories."""

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.customer_memory_service.CustomerMemory") as MockModel:
        MockModel.return_value = _make_memory_mock()
        MockModel.customer_id = MagicMock()
        MockModel.key = MagicMock()

        session_memories = {
            "preferred_time": {"value": "mornings", "memory_type": "preference", "confidence": 0.95},
            "pet_count": {"value": "2 dogs", "memory_type": "fact"},
        }

        saved = service.flush_session_memories(
            db=mock_db,
            session_memories=session_memories,
            customer_id=10,
            business_id=1,
            source_session_id="session-xyz",
        )

    assert saved == 2


# ---------------------------------------------------------------------------
# test_flush_session_memories_empty
# ---------------------------------------------------------------------------

def test_flush_session_memories_empty(service, mock_db):
    """flush_session_memories with empty dict should return 0."""

    saved = service.flush_session_memories(
        db=mock_db,
        session_memories={},
        customer_id=10,
        business_id=1,
    )

    assert saved == 0
    mock_db.add.assert_not_called()
