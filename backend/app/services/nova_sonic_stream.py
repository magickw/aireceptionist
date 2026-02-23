"""
Nova Sonic Streaming Session Manager

================================================================================
ARCHITECTURE OVERVIEW
================================================================================

This service manages real-time bidirectional voice conversations using a hybrid
architecture that maximizes browser capabilities while keeping AI reasoning
server-side.

DATA FLOW:
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Browser)                               │
│  ┌──────────────┐                    ┌──────────────┐                      │
│  │  Microphone  │──Audio (PCM16)────│  Speaker     │                      │
│  └──────────────┘                    └──────────────┘                      │
│         │                                     ▲                             │
│         ▼                                     │                             │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │         Web Speech API (Browser Native STT)              │              │
│  │  - Zero server cost                                      │              │
│  │  - No audio upload latency                               │              │
│  │  - Chrome/Edge/Safari support                            │              │
│  └──────────────────────┬──────────────────────────────────┘              │
│                         │ Text Transcript                                         │
└─────────────────────────┼────────────────────────────────────────────────────┘
                          │ WebSocket (text)
┌─────────────────────────┼────────────────────────────────────────────────────┐
│                         ▼                                                     │
│              SERVER (FastAPI + Python)                                         │
│  ┌──────────────────────────────────────────────────────────┐               │
│  │         NovaSonicStreamSession                            │               │
│  │                                                            │               │
│  │  1. Safety Checker (Deterministic Triggers)                │               │
│  │     - Critical keywords (911, emergency, lawsuit)          │               │
│  │     - VIP customer detection                               │               │
│  │     - Industry-specific triggers (medical, HVAC, legal)    │               │
│  │                                                            │               │
│  │  2. Reasoning Engine (AWS Bedrock Nova Lite)               │               │
│  │     - Intent classification                                │               │
│  │     - Entity extraction                                    │               │
│  │     - Action selection (15+ available actions)             │               │
│  │     - Tool calls (bookAppointment, placeOrder, etc.)       │               │
│  │                                                            │               │
│  │  3. Streaming Response (converse_stream API)               │               │
│  │     - Real-time text generation                            │               │
│  │     - Thinking block filtering                            │               │
│  │     - Tool call handling                                  │               │
│  │     - Event queuing (text, tools, transcripts, audio)      │               │
│  │                                                            │               │
│  │  4. TTS Synthesis (Amazon Polly)                          │               │
│  │     - Neural voice (16kHz PCM16)                          │               │
│  │     - Base64 encoding for WebSocket                        │               │
│  └──────────────────────┬─────────────────────────────────────┘               │
│                         │ Audio (Base64)                                             │
└─────────────────────────┼────────────────────────────────────────────────────┘
                          │ WebSocket (audio)
                          ▼
                    ┌──────────────┐
                    │  Speaker     │
                    └──────────────┘

================================================================================
KEY COMPONENTS
================================================================================

1. StreamLatencyTracker
   - Tracks time_to_first_chunk_ms and total_latency_ms
   - Monitors streaming performance

2. NovaSonicStreamSession
   - Manages one complete voice conversation session
   - Handles audio buffering and transcript generation
   - Implements safety checks before model invocation
   - Manages conversation history for context
   - Provides async generators for real-time streaming

3. Queues (4 parallel event streams)
   - text_queue: Streaming text chunks from Nova
   - tool_queue: Tool calls requiring execution
   - transcript_queue: User speech transcripts
   - audio_queue: Synthesized audio for playback

================================================================================
SESSION LIFECYCLE
================================================================================

1. Initialization:
   session = NovaSonicStreamSession(
       session_id="unique-id",
       system_prompt=build_prompt(...),
       tool_definitions=[...],
       safety_checker=check_deterministic_triggers
   )
   await session.initialize()

2. Voice Turn:
   await session.start_user_turn()
   await session.send_audio_chunk(chunk1)  # Multiple chunks
   await session.send_audio_chunk(chunk2)
   await session.end_user_turn()  # Triggers STT + reasoning

3. Text Turn:
   await session.send_text_message("Hello")  # Direct text input

4. Tool Result:
   await session.send_tool_result(tool_use_id, result)

5. Cleanup:
   await session.close()

================================================================================
THINKING BLOCK FILTERING
================================================================================

Nova models may emit <thinking>...</thinking> blocks that should be hidden from
end users. The filter handles:

- Complete blocks within a single chunk
- Blocks spanning multiple chunks
- Partial tags at chunk boundaries
- Buffer flushing at turn end

State machine:
  OUTSIDE_BLOCK → sees "<thinking>" → INSIDE_BLOCK → sees "</thinking>" → OUTSIDE_BLOCK

================================================================================
THREAD POOL EXECUTION
================================================================================

The boto3 converse_stream() call is synchronous (blocking). To avoid blocking
the async event loop, we execute it in a ThreadPoolExecutor:

  loop.run_in_executor(_executor, _read_stream)

The thread reads stream events and pushes them to an asyncio.Queue via
loop.call_soon_threadsafe(). The main async loop then processes events from
the queue.

================================================================================
SAFETY ARCHITECTURE
================================================================================

Layer 1: Deterministic Triggers (Pre-Model)
  - Runs BEFORE any model invocation
  - Keyword-based (emergency, lawsuit, 911, etc.)
  - Customer history (repeat complaints, VIP status)
  - Industry-specific (medical symptoms, gas leaks, urgent legal)

Layer 2: Model-Based Safety (Post-Model)
  - Confidence thresholds (industry-specific)
  - Escalation risk scoring
  - High-risk intent detection
  - Intent validation with classifier

Layer 3: Approval Workflow
  - Human review for high-risk actions
  - ApprovalRequest tracking
  - Manager notification

================================================================================
ERROR HANDLING & FALLBACKS
================================================================================

1. STT Failure:
   - Returns error message: "I couldn't understand that. Could you try again?"
   - Sends turn_complete signal

2. Safety Trigger:
   - Stops model invocation
   - Sends predetermined safety response
   - Emits safety_trigger event

3. Stream Error:
   - Sends error event to client
   - Sends turn_complete signal
   - Session remains active for retry

4. Tool Call:
   - Pauses generation
   - Emits tool event
   - Waits for send_tool_result()
   - Continues generation

================================================================================
PERFORMANCE OPTIMIZATIONS
================================================================================

1. Streaming: converse_stream for real-time text generation
2. Thinking Filter: Reduces latency by blocking internal reasoning
3. Async Queues: Non-blocking event relay
4. Thread Pool: Offloads blocking boto3 calls
5. Lazy Loading: Bedrock client created on first use

================================================================================
USAGE EXAMPLE
================================================================================

from app.services.nova_sonic_stream import (
    NovaSonicStreamSession,
    build_nova_sonic_system_prompt,
    build_tool_definitions
)

# Build context
system_prompt = build_nova_sonic_system_prompt(
    business_context=business_info,
    customer_context=customer_info
)

tool_defs = build_tool_definitions("restaurant", business_info)

# Create session
session = NovaSonicStreamSession(
    session_id="call-123",
    system_prompt=system_prompt,
    tool_definitions=tool_defs,
    safety_checker=check_triggers
)

await session.initialize()

# Process voice
await session.start_user_turn()
await session.send_audio_chunk(audio_chunk1)
await session.send_audio_chunk(audio_chunk2)
await session.end_user_turn()

# Stream responses
async for event in session.text_queue:
    if event and "chunk" in event:
        logger.debug(event["chunk"])

# Cleanup
await session.close()
"""
import boto3
import json
import asyncio
import time
import traceback
from typing import Dict, Any, Optional, Callable, List
from queue import Full as QueueFull
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("nova_sonic_stream")


# Thread pool shared across all streaming sessions
_executor = ThreadPoolExecutor(max_workers=32)


class StreamLatencyTracker:
    """Tracks latency for streaming responses."""
    def __init__(self):
        self._start_time: Optional[float] = None
        self._first_chunk_at: Optional[float] = None
        self._end_time: Optional[float] = None

    def mark_start(self):
        self._start_time = time.monotonic()

    def mark_first_chunk(self):
        if self._first_chunk_at is None:
            self._first_chunk_at = time.monotonic()

    def mark_end(self):
        self._end_time = time.monotonic()

    def get_metrics(self) -> Dict[str, float]:
        metrics = {}
        base = self._start_time
        if base is None:
            return metrics
        if self._first_chunk_at is not None:
            metrics["time_to_first_chunk_ms"] = round((self._first_chunk_at - base) * 1000, 2)
        if self._end_time is not None:
            metrics["total_latency_ms"] = round((self._end_time - base) * 1000, 2)
        return metrics

    def reset(self):
        self._start_time = None
        self._first_chunk_at = None
        self._end_time = None


class NovaSonicStreamSession:
    """
    Manages one streaming session using the AWS Bedrock converse_stream API.

    Audio flow:
      1. Browser sends PCM chunks via WebSocket
      2. send_audio_chunk() buffers them
      3. end_user_turn() transcribes the buffer via Amazon Transcribe,
         runs safety checks, then calls converse_stream for the model response
      4. Text response is streamed to text_queue
      5. After text completes, Polly TTS audio is sent to audio_queue
    """
    def __init__(
        self,
        session_id: str,
        system_prompt: str,
        tool_definitions: Optional[List[Dict[str, Any]]] = None,
        safety_checker: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
        model_id: str = "amazon.nova-lite-v1:0",
    ):
        self.session_id = session_id
        self.system_prompt = system_prompt
        self.tool_definitions = tool_definitions or []
        self.safety_checker = safety_checker
        self.model_id = model_id

        # Queues for dispatching output events
        self.text_queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.tool_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self.transcript_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self.audio_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        # State
        self.is_active = False
        self._response_task: Optional[asyncio.Task] = None
        self.latency = StreamLatencyTracker()
        self._conversation_history: List[Dict[str, Any]] = []

        # Audio buffering (accumulated between start_user_turn / end_user_turn)
        self._audio_buffer = b""

        # Thinking-block filter state (reset per assistant turn)
        self._in_thinking_block = False
        self._partial_text = ""

        # Bedrock client
        self._bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    async def initialize(self):
        """Initialize the streaming session."""
        self.is_active = True

    # ------------------------------------------------------------------
    # User turn lifecycle
    # ------------------------------------------------------------------

    async def start_user_turn(self):
        """Mark beginning of a new user voice turn. Resets audio buffer."""
        self._audio_buffer = b""
        self._partial_text = ""
        self._in_thinking_block = False
        self.latency.reset()
        self.latency.mark_start()

    async def send_audio_chunk(self, audio_data: bytes):
        """Buffer an audio chunk. STT happens later in end_user_turn()."""
        self._audio_buffer += audio_data

    async def end_user_turn(self):
        """
        Transcribe buffered audio, run safety checks, then generate a
        model response via converse_stream.
        """
        audio_len = len(self._audio_buffer) if self._audio_buffer else 0
        logger.info(f"end_user_turn called with {audio_len} bytes of audio")

        if not self._audio_buffer or len(self._audio_buffer) < 1000:
            logger.warning(f"Audio buffer too small ({audio_len} bytes), skipping transcription")
            return

        audio_data = self._audio_buffer
        self._audio_buffer = b""

        # --- STT ---
        from app.services.nova_sonic import nova_sonic
        logger.info("Calling transcription service...")
        
        # Callback to send partial transcripts for live preview
        async def on_partial_transcript(text: str, is_partial: bool = False):
            # Send partial transcript for live preview (both partial and final updates)
            try:
                self.transcript_queue.put_nowait({"text": text, "is_partial": is_partial})
            except asyncio.QueueFull:
                logger.warning("transcript_queue full, dropping partial transcript")
        
        transcript = await nova_sonic._transcribe_audio_with_nova(audio_data, on_partial=on_partial_transcript)
        logger.info(f"Transcription result: '{transcript[:100] if transcript else 'EMPTY'}...'")

        if not transcript:
            logger.warning("Empty transcript, sending fallback response")
            # Provide helpful fallback message suggesting text input
            await self.text_queue.put({
                "chunk": "I'm having trouble understanding your voice right now. Could you please type your request or try speaking again more clearly?",
            })
            await self.text_queue.put({"turn_complete": True})
            return

        # Emit transcript to client
        logger.info(f"Sending transcript to client: {transcript}")
        try:
            self.transcript_queue.put_nowait({"text": transcript})
        except asyncio.QueueFull:
            logger.warning("transcript_queue full, dropping final transcript")

        # --- Safety check ---
        if self.safety_checker:
            logger.info(f"[nova_sonic_stream] Running safety check on transcript: {transcript[:50]}...")
            safety_result = self.safety_checker(transcript)
            logger.info(f"[nova_sonic_stream] Safety check result: {safety_result}")
            # Only skip AI response if should_escalate is True
            if safety_result and safety_result.get('should_escalate'):
                logger.info(f"[nova_sonic_stream] Safety trigger detected, skipping AI response")
                try:
                    self.transcript_queue.put_nowait({
                        "text": transcript,
                        "safety_trigger": safety_result,
                    })
                except asyncio.QueueFull:
                    logger.warning("transcript_queue full, dropping safety transcript")
                await self.text_queue.put({"turn_complete": True})
                return

        # Add to conversation history and generate response
        self._conversation_history.append({
            "role": "user",
            "content": [{"text": transcript}],
        })
        logger.info(f"[nova_sonic_stream] About to call _generate_assistant_response for transcript: {transcript}")
        await self._generate_assistant_response()
        logger.info(f"[nova_sonic_stream] _generate_assistant_response completed")

    # ------------------------------------------------------------------
    # Text input (for text-mode conversations)
    # ------------------------------------------------------------------

    async def send_text_message(self, message: str):
        """Send a text message directly (for text-based conversations)."""
        self._conversation_history.append({
            "role": "user",
            "content": [{"text": message}],
        })
        await self._generate_assistant_response()

    # ------------------------------------------------------------------
    # Tool result
    # ------------------------------------------------------------------

    async def send_tool_result(self, tool_use_id: str, result: Dict[str, Any]):
        """Send tool result back to the model and continue generation."""
        self._conversation_history.append({
            "role": "user",
            "content": [{
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"text": json.dumps(result)}],
                    "status": "success",
                },
            }],
        })
        await self._generate_assistant_response()

    # ------------------------------------------------------------------
    # Core: stream model response
    # ------------------------------------------------------------------

    def _open_stream(
        self,
        messages: List[Dict[str, Any]],
        tool_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Open a converse_stream request (blocking boto3 call)."""
        kwargs: Dict[str, Any] = {
            "modelId": self.model_id,
            "messages": messages,
        }
        if self.system_prompt:
            kwargs["system"] = [{"text": self.system_prompt}]
        kwargs["inferenceConfig"] = {
            "maxTokens": 1024,
            "temperature": 0.7,
            "topP": 0.9,
        }
        if tool_config:
            kwargs["toolConfig"] = tool_config
        return self._bedrock.converse_stream(**kwargs)

    async def _generate_assistant_response(self):
        """
        Stream a model response via converse_stream.

        Runs the blocking boto3 iteration in a thread pool and bridges
        events to asyncio queues.
        """
        logger.info(f"[nova_sonic_stream] _generate_assistant_response called!")
        # Reset thinking-block state for this turn
        self._in_thinking_block = False
        self._partial_text = ""

        try:
            # Build tool config
            tool_config = None
            if self.tool_definitions:
                tool_config = {
                    "tools": [
                        {
                            "toolSpec": {
                                "name": t["name"],
                                "description": t.get("description", ""),
                                "inputSchema": t.get("inputSchema", {}),
                            }
                        }
                        for t in self.tool_definitions
                    ]
                }
            
            logger.info(f"[nova_sonic_stream] Generating assistant response with {len(self._conversation_history)} messages in history")
            logger.info(f"[nova_sonic_stream] System prompt: {self.system_prompt[:100] if self.system_prompt else 'None'}...")

            # Bridge blocking stream -> async via an intermediate queue
            loop = asyncio.get_event_loop()
            event_queue: asyncio.Queue = asyncio.Queue()

            def _read_stream():
                try:
                    resp = self._open_stream(self._conversation_history, tool_config)
                    for ev in resp["stream"]:
                        loop.call_soon_threadsafe(event_queue.put_nowait, ev)
                except Exception as e:
                    loop.call_soon_threadsafe(
                        event_queue.put_nowait, {"_error": str(e)}
                    )
                finally:
                    loop.call_soon_threadsafe(event_queue.put_nowait, None)

            loop.run_in_executor(_executor, _read_stream)

            # --- Process events from the thread ---
            accumulated_text = ""
            current_tool_use_id: Optional[str] = None
            current_tool_name: Optional[str] = None
            current_tool_input_json = ""
            in_tool_block = False
            stop_reason: Optional[str] = None

            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    await self.text_queue.put({"error": "Stream timeout"})
                    await self.text_queue.put({"turn_complete": True})
                    break
                if event is None:
                    break
                if not self.is_active:
                    break
                if "_error" in event:
                    logger.error(f"Stream error: {event['_error']}")
                    await self.text_queue.put({"error": event["_error"]})
                    break

                # --- contentBlockStart ---
                if "contentBlockStart" in event:
                    start_info = event["contentBlockStart"].get("start", {})
                    if "toolUse" in start_info:
                        in_tool_block = True
                        current_tool_use_id = start_info["toolUse"].get("toolUseId", "")
                        current_tool_name = start_info["toolUse"].get("name", "")
                        current_tool_input_json = ""

                # --- contentBlockDelta ---
                elif "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})

                    if in_tool_block:
                        # Tool use input chunk
                        input_chunk = delta.get("toolUse", {}).get("input", "")
                        current_tool_input_json += input_chunk
                    else:
                        # Text delta
                        text = delta.get("text", "")
                        if text:
                            filtered = self._filter_thinking(text)
                            if filtered:
                                self.latency.mark_first_chunk()
                                accumulated_text += filtered
                                await self.text_queue.put({"chunk": filtered})

                # --- contentBlockStop ---
                elif "contentBlockStop" in event:
                    if in_tool_block and current_tool_name:
                        # Parse accumulated tool input JSON
                        try:
                            tool_input = (
                                json.loads(current_tool_input_json)
                                if current_tool_input_json
                                else {}
                            )
                        except json.JSONDecodeError:
                            tool_input = {}

                        await self.tool_queue.put({
                            "tool_use_id": current_tool_use_id,
                            "name": current_tool_name,
                            "input": tool_input,
                        })

                        # Record tool use in conversation history
                        self._conversation_history.append({
                            "role": "assistant",
                            "content": [{
                                "toolUse": {
                                    "toolUseId": current_tool_use_id,
                                    "name": current_tool_name,
                                    "input": tool_input,
                                }
                            }],
                        })

                        in_tool_block = False
                        current_tool_use_id = None
                        current_tool_name = None
                        current_tool_input_json = ""
                    else:
                        # Flush any remaining partial text from thinking filter
                        remainder = self._flush_thinking_buffer()
                        if remainder:
                            accumulated_text += remainder
                            await self.text_queue.put({"chunk": remainder})

                # --- messageStop ---
                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason", "")
                    self.latency.mark_end()
                    break

            # Record assistant text in conversation history
            if accumulated_text:
                self._conversation_history.append({
                    "role": "assistant",
                    "content": [{"text": accumulated_text}],
                })

            # If stop_reason is tool_use, the relay task will call send_tool_result()
            # which re-enters _generate_assistant_response(). Don't finalize yet.
            if stop_reason == "tool_use":
                return

            # --- Turn complete ---
            await self.text_queue.put({"turn_complete": True})

            # --- TTS: synthesize audio for the full text response ---
            if accumulated_text:
                from app.services.nova_sonic import nova_sonic
                logger.info(f"[nova_sonic_stream] Synthesizing speech for: {accumulated_text[:100]}...")
                audio_data = await nova_sonic._synthesize_speech(accumulated_text)
                if audio_data:
                    audio_b64 = nova_sonic.encode_audio_base64(audio_data)
                    try:
                        await asyncio.wait_for(
                            self.audio_queue.put({
                                "audio": audio_b64,
                                "sample_rate": 16000,
                            }),
                            timeout=5.0,
                        )
                    except asyncio.TimeoutError:
                        logger.warning("audio_queue full, dropping TTS audio chunk")
            else:
                logger.warning(f"[nova_sonic_stream] accumulated_text is None or empty, skipping TTS")

        except Exception as e:
            logger.error(f"Error: {e}\n{traceback.format_exc()}")
            await self.text_queue.put({"error": str(e)})
            await self.text_queue.put({"turn_complete": True})

    # ------------------------------------------------------------------
    # Thinking-block filter
    # ------------------------------------------------------------------

    def _filter_thinking(self, text: str) -> str:
        """
        Filter out <thinking>...</thinking> blocks that may span multiple
        chunks. Returns the portion of text that should be emitted.
        Also sends thinking content to frontend for display.
        """
        self._partial_text += text
        output = ""

        while True:
            if not self._in_thinking_block:
                idx = self._partial_text.find("<thinking>")
                if idx != -1:
                    output += self._partial_text[:idx]
                    self._partial_text = self._partial_text[idx + 10:]
                    self._in_thinking_block = True
                    continue
                elif self._partial_text and self._is_partial_tag(self._partial_text, "<thinking>"):
                    # Might be a partial tag; hold back
                    break
                else:
                    output += self._partial_text
                    self._partial_text = ""
                    break
            else:
                idx = self._partial_text.find("</thinking>")
                if idx != -1:
                    # Capture and send the thinking content
                    thinking_content = self._partial_text[:idx].strip()
                    if thinking_content:
                        asyncio.create_task(self.text_queue.put({"thinking": thinking_content}))
                    self._partial_text = self._partial_text[idx + 11:]
                    self._in_thinking_block = False
                    continue
                elif self._partial_text and self._is_partial_tag(self._partial_text, "</thinking>"):
                    break
                else:
                    # Still inside thinking; discard
                    self._partial_text = ""
                    break

        return output
    
    def _is_partial_tag(self, text: str, full_tag: str) -> bool:
        """Check if text ends with a partial version of full_tag."""
        if not text:
            return False
        # Check if any suffix of text is a prefix of full_tag
        for i in range(1, len(full_tag)):
            if text.endswith(full_tag[:i]):
                return True
        return False

    def _flush_thinking_buffer(self) -> str:
        """Flush remaining partial text (called at content block end)."""
        if self._partial_text and not self._in_thinking_block:
            if "<thinking" not in self._partial_text:
                out = self._partial_text
                self._partial_text = ""
                return out
        self._partial_text = ""
        return ""

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self):
        """Close the streaming session."""
        if not self.is_active:
            return
        self.is_active = False

        if self._response_task and not self._response_task.done():
            self._response_task.cancel()
            try:
                await self._response_task
            except (asyncio.CancelledError, Exception):
                pass

        # Sentinel values to unblock relay consumers
        await self.text_queue.put(None)
        await self.tool_queue.put(None)
        await self.transcript_queue.put(None)
        await self.audio_queue.put(None)


# ======================================================================
# Prompt & tool builders (used by nova_sonic.create_streaming_session)
# ======================================================================

def build_nova_sonic_system_prompt(
    business_context: Dict[str, Any],
    customer_context: Dict[str, Any],
    knowledge_context: str = "",
    training_context: str = "",
) -> str:
    """Build the system prompt for Nova Sonic voice conversations."""
    business_name = business_context.get("name", "our business")
    business_type = business_context.get("type", "general")
    business_phone = business_context.get("phone", "")
    business_address = business_context.get("address", "")
    business_website = business_context.get("website", "")
    services = business_context.get("services", [])
    menu = business_context.get("menu", [])
    hours = business_context.get("hours", {})

    customer_name = customer_context.get("name", "Unknown")
    
    # Use custom welcome message if provided
    custom_welcome = business_context.get("welcome_message", "")

    prompt = f"""You are an AI voice receptionist for {business_name}, a {business_type} business.

Your role is to:
- Provide friendly, professional customer service via voice
- Answer questions about the business, services, and hours
- Help customers book appointments
- Take orders for products or services
- Transfer to a human when needed

"""

    # Add custom welcome instruction if provided
    if custom_welcome:
        prompt += f"""Custom Greeting: {custom_welcome}

When you first greet the customer, use this message: "{custom_welcome}"

"""

    prompt += f"""Business Information:
- Name: {business_name}
- Type: {business_type}
"""

    if business_phone:
        prompt += f"- Phone: {business_phone}\n"

    if business_address:
        prompt += f"- Address: {business_address}\n"

    if business_website:
        prompt += f"- Website: {business_website}\n"

    if services:
        prompt += f"- Services: {', '.join(services)}\n"

    # Only show menu items for businesses that actually have menus (restaurants, retail, etc.)
    # Hotels don't have menus - they have room types which are handled differently
    if menu and business_type not in ["hotel", "dental", "medical", "law_firm", "accounting", "real_estate", "hvac"]:
        menu_items = ", ".join(
            [f"{item.get('name', '')} (${item.get('price', 0)})" for item in menu[:10]]
        )
        prompt += f"- Menu Items: {menu_items}\n"

    if hours:
        prompt += f"- Hours: {json.dumps(hours)}\n"

    prompt += f"""

Current Customer:
- Name: {customer_name}
"""

    # Add business-specific booking flow instructions
    from app.services.business_templates import BusinessTypeTemplate
    booking_flow = BusinessTypeTemplate.get_booking_flow(business_type)
    
    if booking_flow and booking_flow.get("steps"):
        steps = booking_flow.get("steps", [])
        required_fields = [step["field"] for step in steps if step.get("ask_if_missing", True)]
        
        prompt += f"""

Booking Instructions for {business_type.title()}:
Before booking, you MUST collect the following information from the customer:
{chr(10).join([f"- {field}" for field in required_fields])}

**DO NOT book until ALL required information is collected.**
Ask for each piece of information naturally, one at a time.
"""

    if knowledge_context:
        prompt += f"\nKnowledge Base:\n{knowledge_context}\n"

    if training_context:
        prompt += f"\n{training_context}\n"

    prompt += """
Voice Interaction Guidelines:
- Keep responses conversational and natural (like a real person speaking)
- Use clear, simple language
- Avoid overly technical terms
- Be concise but friendly
- Ask clarifying questions when needed
- If you don't know the answer, offer to transfer to a human
- Respond directly without thinking or analysis steps - just provide the helpful response
- **NEVER repeat questions** - If customer already provided information, don't ask again
- **For hotels: When a customer wants to extend their stay, ask for their name and room number FIRST, then look up their reservation before asking about the extension**

When a customer wants to:
"""

    return prompt


def build_tool_definitions(
    business_type: str, business_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Build tool definitions for Nova Sonic to use."""
    base_tools = [
        {
            "name": "bookAppointment",
            "description": "Book a new appointment for the customer",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "The date for the appointment (e.g., 'tomorrow', 'next Tuesday', 'March 15')",
                        },
                        "time": {
                            "type": "string",
                            "description": "The time for the appointment (e.g., '2pm', '10:30 AM')",
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Customer's name",
                        },
                        "customer_phone": {
                            "type": "string",
                            "description": "Customer's phone number",
                        },
                        "service": {
                            "type": "string",
                            "description": "The type of service being booked",
                        },
                    },
                    "required": ["date", "time", "customer_name", "service"],
                }
            },
        },
        {
            "name": "checkAvailability",
            "description": "Check if a specific date/time is available for booking",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "The date to check",
                        },
                        "time": {
                            "type": "string",
                            "description": "The time to check",
                        },
                    },
                    "required": ["date", "time"],
                }
            },
        },
        {
            "name": "placeOrder",
            "description": "Add items to an order",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "quantity": {"type": "integer"},
                                },
                            },
                        },
                        "delivery_method": {
                            "type": "string",
                            "description": "pickup or delivery",
                        },
                    },
                }
            },
        },
        {
            "name": "confirmOrder",
            "description": "Finalize and save the current order",
            "inputSchema": {"json": {"type": "object", "properties": {}}},
        },
        {
            "name": "transferToHuman",
            "description": "Transfer the call to a human agent",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for transfer",
                        }
                    },
                }
            },
        },
        {
            "name": "sendDirections",
            "description": "Send directions to the business location",
            "inputSchema": {"json": {"type": "object", "properties": {}}},
        },
        {
            "name": "processPayment",
            "description": "Initiate payment processing",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Payment amount",
                        }
                    },
                }
            },
        },
    ]

    return base_tools
