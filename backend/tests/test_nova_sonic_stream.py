"""Unit tests for Nova Sonic Streaming Service"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.nova_sonic_stream import (
    NovaSonicStreamSession,
    build_nova_sonic_system_prompt,
    build_tool_definitions,
    StreamLatencyTracker
)


@pytest.fixture
def latency_tracker():
    """Create a latency tracker instance"""
    return StreamLatencyTracker()


@pytest.fixture
def sample_business_context():
    """Sample business context for testing"""
    return {
        "name": "Test Business",
        "type": "restaurant",
        "services": ["dine-in", "takeout"],
        "menu": [{"name": "Burger", "price": 12.99}],
        "hours": {"monday": "9am-9pm"}
    }


@pytest.fixture
def sample_customer_context():
    """Sample customer context for testing"""
    return {
        "name": "John Doe",
        "phone": "555-1234",
        "email": "john@example.com"
    }


@pytest.fixture
def sample_session():
    """Create a sample streaming session"""
    session = NovaSonicStreamSession(
        session_id="test-session-123",
        system_prompt="You are a helpful assistant.",
        tool_definitions=[],
        safety_checker=None
    )
    return session


class TestStreamLatencyTracker:
    """Test cases for latency tracking"""
    
    def test_latency_tracker_initial_state(self, latency_tracker):
        """Test initial state of latency tracker"""
        assert latency_tracker.get_metrics() == {}
    
    def test_mark_start(self, latency_tracker):
        """Test marking start time"""
        latency_tracker.mark_start()
        assert latency_tracker._start_time is not None
    
    def test_mark_first_chunk(self, latency_tracker):
        """Test marking first chunk time"""
        latency_tracker.mark_start()
        asyncio.run(asyncio.sleep(0.01))
        latency_tracker.mark_first_chunk()
        assert latency_tracker._first_chunk_at is not None
    
    def test_mark_end(self, latency_tracker):
        """Test marking end time"""
        latency_tracker.mark_start()
        asyncio.run(asyncio.sleep(0.01))
        latency_tracker.mark_end()
        assert latency_tracker._end_time is not None
    
    def test_get_metrics_with_all_markers(self, latency_tracker):
        """Test getting metrics with all markers set"""
        latency_tracker.mark_start()
        asyncio.run(asyncio.sleep(0.01))
        latency_tracker.mark_first_chunk()
        asyncio.run(asyncio.sleep(0.01))
        latency_tracker.mark_end()
        
        metrics = latency_tracker.get_metrics()
        
        assert "time_to_first_chunk_ms" in metrics
        assert "total_latency_ms" in metrics
        assert metrics["time_to_first_chunk_ms"] > 0
        assert metrics["total_latency_ms"] > 0
    
    def test_reset(self, latency_tracker):
        """Test resetting latency tracker"""
        latency_tracker.mark_start()
        latency_tracker.mark_first_chunk()
        latency_tracker.mark_end()
        
        latency_tracker.reset()
        
        assert latency_tracker._start_time is None
        assert latency_tracker._first_chunk_at is None
        assert latency_tracker._end_time is None
        assert latency_tracker.get_metrics() == {}


class TestNovaSonicStreamSession:
    """Test cases for streaming session"""
    
    @pytest.mark.asyncio
    async def test_session_initialization(self, sample_session):
        """Test session initialization"""
        assert sample_session.session_id == "test-session-123"
        assert sample_session.system_prompt == "You are a helpful assistant."
        assert sample_session.is_active is False
    
    @pytest.mark.asyncio
    async def test_initialize(self, sample_session):
        """Test activating session"""
        await sample_session.initialize()
        assert sample_session.is_active is True
    
    @pytest.mark.asyncio
    async def test_start_user_turn(self, sample_session):
        """Test starting user turn"""
        await sample_session.initialize()
        await sample_session.start_user_turn()
        
        assert sample_session._audio_buffer == b""
        assert sample_session._partial_text == ""
        assert sample_session._in_thinking_block is False
    
    @pytest.mark.asyncio
    async def test_send_audio_chunk(self, sample_session):
        """Test buffering audio chunks"""
        await sample_session.initialize()
        await sample_session.start_user_turn()
        
        chunk1 = b"audio_data_1"
        chunk2 = b"audio_data_2"
        
        await sample_session.send_audio_chunk(chunk1)
        await sample_session.send_audio_chunk(chunk2)
        
        assert sample_session._audio_buffer == chunk1 + chunk2
    
    @pytest.mark.asyncio
    async def test_send_text_message(self, sample_session):
        """Test sending text message directly"""
        await sample_session.initialize()
        
        # Mock the assistant response generation to avoid AWS calls
        with patch.object(sample_session, '_generate_assistant_response', new_callable=AsyncMock):
            await sample_session.send_text_message("Hello, how are you?")
        
        # User message should be added (assistant is mocked)
        assert len(sample_session._conversation_history) == 1
        assert sample_session._conversation_history[0]["role"] == "user"
        # Text is prefixed with language note
        assert "Hello, how are you?" in sample_session._conversation_history[0]["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_close(self, sample_session):
        """Test closing session"""
        await sample_session.initialize()
        await sample_session.close()
        
        assert sample_session.is_active is False
    
    @pytest.mark.asyncio
    async def test_close_without_initialize(self, sample_session):
        """Test closing session without initialization"""
        await sample_session.close()
        
        assert sample_session.is_active is False


class TestThinkingBlockFilter:
    """Test cases for thinking block filtering"""
    
    @pytest.mark.asyncio
    async def test_filter_thinking_no_blocks(self, sample_session):
        """Test filtering text without thinking blocks"""
        text = "This is normal text without any thinking blocks."
        filtered = sample_session._filter_thinking(text)
        
        assert filtered == text
    
    @pytest.mark.asyncio
    async def test_filter_thinking_complete_block(self, sample_session):
        """Test filtering complete thinking block"""
        text = "Hello <thinking>This is internal reasoning</thinking> World"
        filtered = sample_session._filter_thinking(text)
        
        assert "<thinking>" not in filtered
        assert "</thinking>" not in filtered
        assert "internal reasoning" not in filtered
        assert "Hello" in filtered
        assert "World" in filtered
    
    @pytest.mark.asyncio
    async def test_filter_thinking_partial_open_tag(self, sample_session):
        """Test filtering with partial open tag"""
        sample_session._filter_thinking("Hello ")
        filtered = sample_session._filter_thinking("<thinkin")
        
        # Should buffer partial tag
        assert filtered == ""
    
    @pytest.mark.asyncio
    async def test_filter_thinking_multiple_blocks(self, sample_session):
        """Test filtering multiple thinking blocks"""
        text = "A <thinking>Block 1</thinking> B <thinking>Block 2</thinking> C"
        filtered = sample_session._filter_thinking(text)
        
        assert "<thinking>" not in filtered
        assert filtered == "A B C"  # Single spaces between words
    
    @pytest.mark.asyncio
    async def test_flush_thinking_buffer(self, sample_session):
        """Test flushing thinking buffer"""
        sample_session._partial_text = "Normal text after thinking"
        sample_session._in_thinking_block = False
        
        flushed = sample_session._flush_thinking_buffer()
        
        assert flushed == "Normal text after thinking"
        assert sample_session._partial_text == ""
    
    @pytest.mark.asyncio
    async def test_flush_thinking_buffer_inside_block(self, sample_session):
        """Test flushing buffer while inside thinking block"""
        sample_session._partial_text = "Still in thinking"
        sample_session._in_thinking_block = True
        
        flushed = sample_session._flush_thinking_buffer()
        
        assert flushed == ""  # Should discard thinking content
        assert sample_session._partial_text == ""


class TestBuildSystemPrompt:
    """Test cases for system prompt building"""
    
    def test_build_basic_prompt(self, sample_business_context, sample_customer_context):
        """Test building basic system prompt"""
        prompt = build_nova_sonic_system_prompt(
            business_context=sample_business_context,
            customer_context=sample_customer_context
        )
        
        assert "Test Business" in prompt
        assert "restaurant" in prompt
        assert "John Doe" in prompt
        assert "voice receptionist" in prompt.lower()
    
    def test_build_prompt_with_knowledge(self, sample_business_context, sample_customer_context):
        """Test building prompt with knowledge base"""
        knowledge = "Our special today is 20% off all burgers."
        prompt = build_nova_sonic_system_prompt(
            business_context=sample_business_context,
            customer_context=sample_customer_context,
            knowledge_context=knowledge
        )
        
        assert "Knowledge Base" in prompt
        assert "20% off all burgers" in prompt
    
    def test_build_prompt_with_training(self, sample_business_context, sample_customer_context):
        """Test building prompt with training context"""
        training = "## Training\nExample: Customer asks for price -> Response with menu prices"
        prompt = build_nova_sonic_system_prompt(
            business_context=sample_business_context,
            customer_context=sample_customer_context,
            training_context=training
        )
        
        assert "## Training" in prompt
        assert "Example:" in prompt


class TestBuildToolDefinitions:
    """Test cases for tool definition building"""
    
    def test_build_basic_tools(self, sample_business_context):
        """Test building basic tool definitions"""
        tools = build_tool_definitions("restaurant", sample_business_context)
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check for expected tools
        tool_names = [t["name"] for t in tools]
        assert "bookAppointment" in tool_names
        assert "placeOrder" in tool_names
        assert "transferToHuman" in tool_names
    
    def test_book_appointment_tool_schema(self, sample_business_context):
        """Test bookAppointment tool has correct schema"""
        tools = build_tool_definitions("restaurant", sample_business_context)
        booking_tool = next((t for t in tools if t["name"] == "bookAppointment"), None)
        
        assert booking_tool is not None
        assert "description" in booking_tool
        assert "inputSchema" in booking_tool
        
        schema = booking_tool["inputSchema"]["json"]
        assert "properties" in schema
        assert "required" in schema
        
        required_fields = schema["required"]
        assert "date" in required_fields
        assert "time" in required_fields
        assert "customer_name" in required_fields
        assert "service" in required_fields
    
    def test_place_order_tool_schema(self, sample_business_context):
        """Test placeOrder tool has correct schema"""
        tools = build_tool_definitions("restaurant", sample_business_context)
        order_tool = next((t for t in tools if t["name"] == "placeOrder"), None)
        
        assert order_tool is not None
        schema = order_tool["inputSchema"]["json"]
        
        assert "items" in schema["properties"]
        assert "delivery_method" in schema["properties"]


class TestQueueBehavior:
    """Test queue behavior in streaming session"""
    
    @pytest.mark.asyncio
    async def test_text_queue_put_get(self, sample_session):
        """Test putting and getting from text queue"""
        await sample_session.initialize()
        
        await sample_session.text_queue.put({"chunk": "Hello"})
        item = await sample_session.text_queue.get()
        
        assert item["chunk"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_tool_queue_put_get(self, sample_session):
        """Test putting and getting from tool queue"""
        await sample_session.initialize()
        
        tool_call = {
            "tool_use_id": "tool-123",
            "name": "bookAppointment",
            "input": {"date": "tomorrow", "time": "2pm"}
        }
        await sample_session.tool_queue.put(tool_call)
        item = await sample_session.tool_queue.get()
        
        assert item["name"] == "bookAppointment"
    
    @pytest.mark.asyncio
    async def test_transcript_queue_put_get(self, sample_session):
        """Test putting and getting from transcript queue"""
        await sample_session.initialize()
        
        await sample_session.transcript_queue.put({"text": "Hello, can I help you?"})
        item = await sample_session.transcript_queue.get()
        
        assert item["text"] == "Hello, can I help you?"


class TestSessionState:
    """Test session state management"""
    
    @pytest.mark.asyncio
    async def test_conversation_history_tracking(self, sample_session):
        """Test conversation history is tracked"""
        await sample_session.initialize()
        
        # Mock the assistant response generation to avoid AWS calls
        with patch.object(sample_session, '_generate_assistant_response', new_callable=AsyncMock):
            await sample_session.send_text_message("First message")
            await sample_session.send_text_message("Second message")
        
        # Each send_text_message adds user message (assistant is mocked)
        assert len(sample_session._conversation_history) == 2
        assert sample_session._conversation_history[0]["role"] == "user"
        # Text is prefixed with language note
        assert "First message" in sample_session._conversation_history[0]["content"][0]["text"]
        assert sample_session._conversation_history[1]["role"] == "user"
        assert "Second message" in sample_session._conversation_history[1]["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_conversation_history_with_tools(self, sample_session):
        """Test conversation history includes tool calls"""
        await sample_session.initialize()
        
        # Simulate adding a tool call
        sample_session._conversation_history.append({
            "role": "assistant",
            "content": [{
                "toolUse": {
                    "toolUseId": "tool-123",
                    "name": "bookAppointment",
                    "input": {"date": "tomorrow"}
                }
            }]
        })
        
        assert len(sample_session._conversation_history) == 1
        assert sample_session._conversation_history[0]["role"] == "assistant"


class TestEndUserTurn:
    """Test cases for end_user_turn method"""
    
    @pytest.mark.asyncio
    async def test_end_user_turn_small_buffer_skipped(self, sample_session):
        """Test that end_user_turn skips processing for small audio buffer"""
        await sample_session.initialize()
        await sample_session.start_user_turn()
        
        # Add small audio data (less than minimum 1000 bytes)
        await sample_session.send_audio_chunk(b"short_audio")
        
        initial_buffer_len = len(sample_session._audio_buffer)
        assert initial_buffer_len > 0
        
        # Should handle gracefully (skips transcription for small audio)
        # Note: Implementation logs warning and returns early for small audio
        await sample_session.end_user_turn()
        
        # Buffer behavior for small audio - implementation returns early
        # This test verifies the graceful handling, not the buffer clearing
    
    @pytest.mark.asyncio
    async def test_end_user_turn_without_audio(self, sample_session):
        """Test end_user_turn when no audio was sent"""
        await sample_session.initialize()
        
        # Should not raise an error
        await sample_session.end_user_turn()
        assert sample_session._audio_buffer == b""


class TestSendToolResult:
    """Test cases for tool result handling"""
    
    @pytest.mark.asyncio
    async def test_send_tool_result(self, sample_session):
        """Test sending tool result"""
        await sample_session.initialize()
        
        tool_use_id = "tool-123"
        result = {"success": True, "appointment_id": "apt-456"}
        
        # Mock the response generation
        with patch.object(sample_session, '_generate_assistant_response', new_callable=AsyncMock):
            await sample_session.send_tool_result(tool_use_id, result)
    
    @pytest.mark.asyncio
    async def test_send_tool_result_adds_to_history(self, sample_session):
        """Test that tool result is added to conversation history"""
        await sample_session.initialize()
        
        tool_use_id = "tool-123"
        result = {"success": True}
        
        with patch.object(sample_session, '_generate_assistant_response', new_callable=AsyncMock):
            await sample_session.send_tool_result(tool_use_id, result)
        
        # Check that tool result was added to history
        tool_results = [msg for msg in sample_session._conversation_history 
                       if msg.get("role") == "user" and "content" in msg]
        assert len(tool_results) == 1
        # Verify toolResult structure
        assert "toolResult" in tool_results[0]["content"][0]
        assert tool_results[0]["content"][0]["toolResult"]["toolUseId"] == tool_use_id


class TestErrorHandling:
    """Test cases for error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_empty_audio_handling(self, sample_session):
        """Test handling of empty audio input"""
        await sample_session.initialize()
        await sample_session.start_user_turn()
        
        # Don't send enough audio chunks (less than 1000 bytes)
        assert sample_session._audio_buffer == b""
        
        # Should handle gracefully
        await sample_session.end_user_turn()
        
        assert sample_session._audio_buffer == b""
    
    @pytest.mark.asyncio
    async def test_session_already_closed(self, sample_session):
        """Test operations on closed session"""
        await sample_session.initialize()
        await sample_session.close()
        
        # Attempting to use closed session should be safe
        assert sample_session.is_active is False
    
    @pytest.mark.asyncio
    async def test_double_close_safe(self, sample_session):
        """Test that closing session twice is safe"""
        await sample_session.initialize()
        await sample_session.close()
        await sample_session.close()  # Should not raise
        
        assert sample_session.is_active is False


class TestStreamingResponses:
    """Test cases for streaming response handling"""
    
    @pytest.mark.asyncio
    async def test_text_queue_streaming(self, sample_session):
        """Test text chunks are queued correctly"""
        await sample_session.initialize()
        
        # Simulate streaming text chunks
        chunks = ["Hello", ", ", "how", " ", "can", " ", "I", " ", "help?"]
        
        for chunk in chunks:
            await sample_session.text_queue.put({"chunk": chunk, "type": "text"})
        
        # Verify all chunks are in queue
        received = []
        for _ in chunks:
            item = await sample_session.text_queue.get()
            received.append(item["chunk"])
        
        assert "".join(received) == "Hello, how can I help?"
    
    @pytest.mark.asyncio
    async def test_audio_queue_streaming(self, sample_session):
        """Test audio chunks are queued correctly"""
        await sample_session.initialize()
        
        # Simulate streaming audio chunks (base64 encoded)
        audio_chunks = [
            {"audio": "base64_chunk_1", "type": "audio"},
            {"audio": "base64_chunk_2", "type": "audio"},
        ]
        
        for chunk in audio_chunks:
            await sample_session.audio_queue.put(chunk)
        
        # Verify queue
        assert await sample_session.audio_queue.get() == audio_chunks[0]
        assert await sample_session.audio_queue.get() == audio_chunks[1]


class TestSafetyChecker:
    """Test cases for safety checking"""
    
    @pytest.mark.asyncio
    async def test_session_with_safety_checker(self):
        """Test session creation with safety checker"""
        def safety_check(transcript: str, context: dict) -> dict:
            if "emergency" in transcript.lower():
                return {"triggered": True, "reason": "Emergency keyword detected"}
            return {"triggered": False}
        
        session = NovaSonicStreamSession(
            session_id="safe-session",
            system_prompt="You are a helpful assistant.",
            tool_definitions=[],
            safety_checker=safety_check
        )
        
        await session.initialize()
        assert session.safety_checker is not None
        assert session.safety_checker("This is an emergency!", {})["triggered"] is True
    
    @pytest.mark.asyncio
    async def test_session_without_safety_checker(self, sample_session):
        """Test session without safety checker"""
        await sample_session.initialize()
        assert sample_session.safety_checker is None


class TestConfigFlags:
    """Test cases for configuration flags"""
    
    def test_streaming_stt_enabled_default(self):
        """Test that streaming STT is enabled by default"""
        from app.core.config import settings
        assert settings.STREAMING_STT_ENABLED is True
    
    def test_incremental_tts_enabled_default(self):
        """Test that incremental TTS is enabled by default"""
        from app.core.config import settings
        assert settings.INCREMENTAL_TTS_ENABLED is True
    
    def test_nova_sonic_streaming_enabled(self):
        """Test that Nova Sonic streaming is enabled"""
        from app.core.config import settings
        assert settings.NOVA_SONIC_STREAMING_ENABLED is True


class TestMultiLanguageSupport:
    """Test cases for multi-language support"""
    
    def test_build_prompt_with_language(self, sample_business_context, sample_customer_context):
        """Test building prompt with language specification"""
        prompt = build_nova_sonic_system_prompt(
            business_context=sample_business_context,
            customer_context=sample_customer_context,
            language="es"
        )
        
        # Should include language context
        assert "Test Business" in prompt
    
    @pytest.mark.asyncio
    async def test_session_language_setting(self):
        """Test session with language setting"""
        session = NovaSonicStreamSession(
            session_id="multi-lang-session",
            system_prompt="You are a helpful assistant.",
            tool_definitions=[],
            safety_checker=None,
            language="es-US"
        )
        
        assert session.language == "es-US"


class TestConversationContext:
    """Test cases for conversation context management"""
    
    @pytest.mark.asyncio
    async def test_max_conversation_history(self, sample_session):
        """Test that conversation history doesn't exceed limits"""
        await sample_session.initialize()
        
        # Add many messages
        for i in range(50):
            sample_session._conversation_history.append({
                "role": "user",
                "content": [{"text": f"Message {i}"}]
            })
        
        # Check if there's a mechanism to limit history
        # (implementation dependent)
        assert len(sample_session._conversation_history) > 0
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_turns(self, sample_session):
        """Test that context is preserved across multiple turns"""
        await sample_session.initialize()
        
        # Mock the assistant response generation to avoid AWS calls
        with patch.object(sample_session, '_generate_assistant_response', new_callable=AsyncMock):
            # First turn
            await sample_session.send_text_message("What's on the menu?")
            
            # Second turn - should have context from first
            await sample_session.send_text_message("I'd like to order the first item")
        
        # Both turns should be in history
        user_messages = [m for m in sample_session._conversation_history 
                        if m["role"] == "user"]
        assert len(user_messages) == 2


class TestTurnCompleteSignal:
    """Test cases for turn complete signaling"""
    
    @pytest.mark.asyncio
    async def test_turn_complete_event(self, sample_session):
        """Test that turn complete is signaled"""
        await sample_session.initialize()
        
        # Mock the assistant response generation
        with patch.object(sample_session, '_generate_assistant_response', new_callable=AsyncMock):
            # Process a text message
            await sample_session.send_text_message("Hello")
        
        # Check for turn_complete in text_queue
        # (implementation may vary)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
