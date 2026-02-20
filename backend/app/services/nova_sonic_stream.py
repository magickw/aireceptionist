"""
Nova Sonic Bidirectional Streaming Session Manager

Replaces the batch STT -> Reasoning -> TTS pipeline with a single
persistent bidirectional stream using Amazon Nova Sonic's native
InvokeModelWithBidirectionalStream API.

Target: 5-30s latency -> sub-1s first audio byte.
"""
import boto3
import json
import base64
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.services.business_templates import BusinessTypeTemplate


# Thread pool shared across all streaming sessions
_executor = ThreadPoolExecutor(max_workers=8)


class StreamLatencyTracker:
    """Tracks first-byte latency for streaming voice turns."""

    def __init__(self):
        self._audio_received_at: Optional[float] = None
        self._first_transcript_at: Optional[float] = None
        self._first_audio_out_at: Optional[float] = None
        self._turn_end_at: Optional[float] = None

    def mark_audio_received(self):
        if self._audio_received_at is None:
            self._audio_received_at = time.monotonic()

    def mark_first_transcript(self):
        if self._first_transcript_at is None:
            self._first_transcript_at = time.monotonic()

    def mark_first_audio_out(self):
        if self._first_audio_out_at is None:
            self._first_audio_out_at = time.monotonic()

    def mark_turn_end(self):
        self._turn_end_at = time.monotonic()

    def get_metrics(self) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        base = self._audio_received_at
        if base is None:
            return metrics
        if self._first_transcript_at is not None:
            metrics["time_to_transcript_ms"] = round(
                (self._first_transcript_at - base) * 1000, 2
            )
        if self._first_audio_out_at is not None:
            metrics["time_to_first_byte_ms"] = round(
                (self._first_audio_out_at - base) * 1000, 2
            )
        if self._turn_end_at is not None:
            metrics["total_turn_ms"] = round(
                (self._turn_end_at - base) * 1000, 2
            )
        return metrics

    def reset(self):
        self._audio_received_at = None
        self._first_transcript_at = None
        self._first_audio_out_at = None
        self._turn_end_at = None


def build_tool_definitions(business_type: str, business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Define tools Nova Sonic can invoke during the conversation.
    Maps to the existing action vocabulary in nova_reasoning.
    """
    tools = [
        {
            "toolSpec": {
                "name": "bookAppointment",
                "description": "Book an appointment for the customer.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "customer_name": {"type": "string", "description": "Customer's full name"},
                            "customer_phone": {"type": "string", "description": "Customer's phone number"},
                            "service": {"type": "string", "description": "Service or reason for appointment"},
                            "date": {"type": "string", "description": "Appointment date (e.g. 'tomorrow', 'March 15')"},
                            "time": {"type": "string", "description": "Appointment time (e.g. '2pm', '10:30 am')"},
                        },
                        "required": ["customer_name", "customer_phone", "date", "time"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "checkAvailability",
                "description": "Check if a time slot is available for an appointment.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Date to check"},
                            "time": {"type": "string", "description": "Time to check"},
                        },
                        "required": ["date", "time"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "transferToHuman",
                "description": "Transfer the call to a human agent for complex or sensitive matters.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "Why transferring to human"},
                        },
                        "required": ["reason"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "sendDirections",
                "description": "Provide directions to the business location.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {},
                    }
                },
            }
        },
    ]

    # Add order tools for business types that support ordering
    if business_type in ("restaurant", "retail"):
        tools.extend([
            {
                "toolSpec": {
                    "name": "placeOrder",
                    "description": "Add items to the customer's order.",
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
                                            "quantity": {"type": "integer", "default": 1},
                                        },
                                        "required": ["name"],
                                    },
                                    "description": "Items to add to the order",
                                },
                                "delivery_method": {
                                    "type": "string",
                                    "enum": ["pickup", "delivery"],
                                    "description": "Pickup or delivery",
                                },
                            },
                            "required": ["items"],
                        }
                    },
                }
            },
            {
                "toolSpec": {
                    "name": "confirmOrder",
                    "description": "Finalize and confirm the current order.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {},
                        }
                    },
                }
            },
        ])

    # Payment tool for business types that handle payments
    tools.append({
        "toolSpec": {
            "name": "processPayment",
            "description": "Initiate payment processing for a given amount.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Amount to charge"},
                    },
                    "required": ["amount"],
                }
            },
        }
    })

    return tools


def build_nova_sonic_system_prompt(
    business_context: Dict[str, Any],
    customer_context: Dict[str, Any],
    knowledge_context: str = "",
    training_context: str = "",
) -> str:
    """
    Adapts the existing system prompt from nova_reasoning for conversational voice.

    Key differences from nova_reasoning._build_system_prompt():
    - No JSON response format (model speaks naturally)
    - Voice-specific guidelines (concise, natural phrasing)
    - Tool-use instructions instead of selected_action field
    """
    business_type = business_context.get("type", "general")
    template_prompt = BusinessTypeTemplate.get_template_prompt(business_type)
    flow_context = BusinessTypeTemplate.get_flow_prompt_context(business_type)
    risk_profile = BusinessTypeTemplate.get_risk_profile(business_type)

    # Build menu section
    menu_section = ""
    menu = business_context.get("menu", [])
    if menu:
        by_category: Dict[str, list] = {}
        for item in menu:
            cat = item.get("category", "Other")
            by_category.setdefault(cat, [])
            price_str = f"${item['price']:.2f}" if item.get("price") else "Price TBD"
            desc = f" ({item['description']})" if item.get("description") else ""
            by_category[cat].append(f"- {item['name']}: {price_str}{desc}")

        menu_lines = []
        for cat, items in by_category.items():
            menu_lines.append(f"\n### {cat}:\n" + "\n".join(items))
        menu_section = f"\n- Menu/Products Available:{''.join(menu_lines)}\n"

    # Build knowledge base section
    kb_section = ""
    if knowledge_context:
        kb_section = f"\n## Knowledge Base:\n{knowledge_context}\n"

    prompt = f"""You are the voice receptionist for {business_context.get('name', 'this business')}.
You are having a real-time phone conversation. Speak naturally and concisely.

## Business Context:
- Business Name: {business_context.get('name', 'Unknown')}
- Business Type: {business_type.title()}
- Services: {', '.join(business_context.get('services', []))}
- Operating Hours: {business_context.get('operating_hours', 'Not specified')}
- Address: {business_context.get('address', 'Not specified')}
{menu_section}

{flow_context}

{template_prompt}

## Customer Context:
- Name: {customer_context.get('name', 'Unknown')}
- Phone: {customer_context.get('phone', 'Unknown')}
- Previous Calls: {customer_context.get('call_count', 0)}
- Satisfaction Score: {customer_context.get('satisfaction_score', 0)}/5.0
{kb_section}
{training_context}

## Voice Conversation Guidelines:
- Keep responses SHORT (1-3 sentences max). This is a phone call, not a text chat.
- Speak naturally as if on the phone. No bullet points, no markdown, no numbered lists.
- Use tools for actions: call bookAppointment to book, placeOrder to take orders, etc.
- Only ask for ONE piece of information at a time.
- Accept information the customer provides without asking them to confirm or repeat.
- If the customer mentions an emergency, safety issue, or asks for a manager,
  use the transferToHuman tool immediately.

## Safety:
- For emergencies (gas leak, fire, chest pain, difficulty breathing):
  Tell the customer to call 911 immediately, then use transferToHuman.
- For legal threats, discrimination, harassment: use transferToHuman.
- High-risk intents for this business type: {', '.join(risk_profile.get('high_risk_intents', []))}
"""
    return prompt


class NovaSonicStreamSession:
    """
    Manages one bidirectional stream per voice call.

    Architecture:
    - Opens a persistent bidirectional stream to Bedrock Nova Sonic
    - Forwards audio chunks in real-time (no buffering)
    - Background task reads output events and dispatches to queues
    - Safety checker runs on every user transcript
    """

    def __init__(
        self,
        session_id: str,
        system_prompt: str,
        tool_definitions: List[Dict[str, Any]],
        safety_checker: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
    ):
        self.session_id = session_id
        self.system_prompt = system_prompt
        self.tool_definitions = tool_definitions
        self.safety_checker = safety_checker

        self.model_id = "amazon.nova-sonic-v1:0"
        self.voice_id = settings.NOVA_SONIC_VOICE_ID
        self.output_sample_rate = settings.NOVA_SONIC_OUTPUT_SAMPLE_RATE

        # Queues for dispatching output events to the WebSocket relay
        self.transcript_queue: asyncio.Queue = asyncio.Queue()
        self.audio_queue: asyncio.Queue = asyncio.Queue()
        self.text_queue: asyncio.Queue = asyncio.Queue()
        self.tool_queue: asyncio.Queue = asyncio.Queue()

        # State
        self.is_active = False
        self._interrupted = False
        self._stream = None
        self._input_stream = None
        self._response_task: Optional[asyncio.Task] = None
        self._content_index = 0
        self._prompt_name_counter = 0
        self.latency = StreamLatencyTracker()

        # Bedrock client
        self._bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    async def initialize(self):
        """
        Open the bidirectional stream and send session setup events.
        """
        loop = asyncio.get_event_loop()

        # Open the bidirectional stream in a thread (boto3 is sync)
        self._stream = await loop.run_in_executor(
            _executor,
            self._open_stream,
        )
        self._input_stream = self._stream.get("body")
        self.is_active = True

        # Send session start
        await self._send_event({
            "event": {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "text": {
                            "maxTokens": 1024,
                            "temperature": 0.7,
                            "topP": 0.9,
                        },
                        "audio": {
                            "outputSampleRate": self.output_sample_rate,
                            "voiceId": self.voice_id,
                        },
                    },
                    "toolUse": {
                        "tools": self.tool_definitions,
                    } if self.tool_definitions else {},
                }
            }
        })

        # Send system prompt
        system_prompt_name = self._next_prompt_name()
        await self._send_event({
            "event": {
                "contentStart": {
                    "promptName": system_prompt_name,
                    "contentIndex": 0,
                    "role": "SYSTEM",
                    "type": "TEXT",
                }
            }
        })
        await self._send_event({
            "event": {
                "textInput": {
                    "promptName": system_prompt_name,
                    "contentIndex": 0,
                    "value": self.system_prompt,
                }
            }
        })
        await self._send_event({
            "event": {
                "contentEnd": {
                    "promptName": system_prompt_name,
                    "contentIndex": 0,
                }
            }
        })

        # Start background response processor
        self._response_task = asyncio.create_task(self._process_responses())

    def _open_stream(self):
        """Synchronous: open the bidirectional stream."""
        return self._bedrock.invoke_model_with_bidirectional_stream(
            modelId=self.model_id,
        )

    def _next_prompt_name(self) -> str:
        self._prompt_name_counter += 1
        return f"prompt-{self._prompt_name_counter}"

    async def _send_event(self, event: Dict[str, Any]):
        """Send an event to the input stream (runs in thread pool)."""
        if not self.is_active or self._input_stream is None:
            return
        loop = asyncio.get_event_loop()
        encoded = json.dumps(event).encode("utf-8")
        await loop.run_in_executor(
            _executor,
            lambda: self._input_stream.send({"chunk": {"bytes": encoded}}),
        )

    async def start_user_turn(self):
        """Mark the beginning of a user audio turn."""
        self._interrupted = False
        self.latency.reset()
        self._content_index += 1
        prompt_name = self._next_prompt_name()
        self._current_user_prompt = prompt_name
        self._current_user_content_index = self._content_index

        await self._send_event({
            "event": {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentIndex": self._content_index,
                    "role": "USER",
                    "type": "AUDIO",
                }
            }
        })

    async def send_audio_chunk(self, audio_bytes: bytes):
        """Forward a single audio chunk immediately to the stream."""
        if not self.is_active:
            return
        self.latency.mark_audio_received()
        prompt_name = getattr(self, "_current_user_prompt", "prompt-1")
        content_index = getattr(self, "_current_user_content_index", 0)

        await self._send_event({
            "event": {
                "audioInput": {
                    "promptName": prompt_name,
                    "contentIndex": content_index,
                    "audio": base64.b64encode(audio_bytes).decode("utf-8"),
                }
            }
        })

    async def end_user_turn(self):
        """Mark the end of a user audio turn."""
        prompt_name = getattr(self, "_current_user_prompt", "prompt-1")
        content_index = getattr(self, "_current_user_content_index", 0)

        await self._send_event({
            "event": {
                "contentEnd": {
                    "promptName": prompt_name,
                    "contentIndex": content_index,
                }
            }
        })

    async def send_tool_result(self, tool_use_id: str, result: Dict[str, Any]):
        """Return a tool execution result to the model."""
        await self._send_event({
            "event": {
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "status": "success",
                    "content": [{"text": json.dumps(result)}],
                }
            }
        })

    async def interrupt(self):
        """
        Called on safety trigger. Discards subsequent model audio.
        The stream stays open so we can send a safety response via Polly fallback.
        """
        self._interrupted = True

    async def _process_responses(self):
        """
        Background task: read output events from the stream and dispatch to queues.
        """
        loop = asyncio.get_event_loop()
        output_stream = self._stream.get("output") if self._stream else None
        if output_stream is None:
            return

        try:
            # Read events in a thread since the iterator is synchronous
            async for event in self._async_iter_output(output_stream):
                if not self.is_active:
                    break

                event_data = event.get("event", event)

                # -- User transcript --
                if "textOutput" in event_data:
                    text_event = event_data["textOutput"]
                    role = text_event.get("role", "")
                    text = text_event.get("value", "")

                    if role == "USER" and text:
                        self.latency.mark_first_transcript()

                        # Run safety checker
                        if self.safety_checker:
                            trigger = self.safety_checker(text)
                            if trigger and trigger.get("should_escalate"):
                                await self.interrupt()
                                await self.transcript_queue.put({
                                    "text": text,
                                    "safety_trigger": trigger,
                                })
                                continue

                        await self.transcript_queue.put({"text": text})

                    elif role == "ASSISTANT" and text:
                        await self.text_queue.put({"chunk": text})

                # -- Audio output --
                elif "audioOutput" in event_data:
                    if self._interrupted:
                        continue  # discard audio after safety interrupt
                    audio_b64 = event_data["audioOutput"].get("audio", "")
                    if audio_b64:
                        self.latency.mark_first_audio_out()
                        await self.audio_queue.put({
                            "audio": audio_b64,
                            "sample_rate": self.output_sample_rate,
                        })

                # -- Tool use request --
                elif "toolUse" in event_data:
                    tool_event = event_data["toolUse"]
                    await self.tool_queue.put({
                        "tool_use_id": tool_event.get("toolUseId", str(uuid.uuid4())),
                        "name": tool_event.get("name", ""),
                        "input": tool_event.get("input", {}),
                    })

                # -- Content end (turn boundary) --
                elif "contentEnd" in event_data:
                    content_end = event_data["contentEnd"]
                    if content_end.get("role") == "ASSISTANT":
                        self.latency.mark_turn_end()

        except Exception as e:
            if self.is_active:
                print(f"[Nova Sonic Stream] Response processor error: {e}")
                self.is_active = False

    async def _async_iter_output(self, output_stream):
        """
        Wraps the synchronous output stream iterator into an async iterator
        using run_in_executor.
        """
        loop = asyncio.get_event_loop()

        def _next_event(iterator):
            try:
                return next(iterator)
            except StopIteration:
                return None

        iterator = iter(output_stream)
        while True:
            event = await loop.run_in_executor(_executor, _next_event, iterator)
            if event is None:
                break
            # Parse the event bytes if needed
            if "chunk" in event:
                chunk_bytes = event["chunk"].get("bytes", b"")
                if chunk_bytes:
                    try:
                        yield json.loads(chunk_bytes)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        yield event
            else:
                yield event

    async def close(self):
        """Send sessionEnd and clean up resources."""
        if not self.is_active:
            return
        self.is_active = False

        try:
            await self._send_event({"event": {"sessionEnd": {}}})
        except Exception:
            pass

        if self._response_task and not self._response_task.done():
            self._response_task.cancel()
            try:
                await self._response_task
            except (asyncio.CancelledError, Exception):
                pass

        # Sentinel values to unblock queue consumers
        await self.transcript_queue.put(None)
        await self.audio_queue.put(None)
        await self.text_queue.put(None)
        await self.tool_queue.put(None)
