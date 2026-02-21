"""
Nova Sonic Streaming Session Manager - Updated for New AWS Bedrock API

Replaces the deprecated invoke_model_with_bidirectional_stream API with the new 
converse_stream API that works with AWS Bedrock's unified API.

IMPORTANT: The new API has limitations:
- nova-sonic-v1:0 does NOT support audio input via the new API (text only)
- Audio input must use Amazon Transcribe separately
- Streaming now only applies to text output (not bidirectional audio)

Architecture:
- Text input → AWS Bedrock Nova Lite → Streaming text response
- Audio input → Amazon Transcribe → Text → AWS Bedrock → Streaming response
"""
import boto3
import json
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings


# Thread pool shared across all streaming sessions
_executor = ThreadPoolExecutor(max_workers=8)


class StreamLatencyTracker:
    """Tracks latency for streaming responses."""
    def __init__(self):
        self._start_time: Optional[float] = None
        self._first_chunk_at: Optional[float] = None
        self._end_time: Optional[float] = None

    def mark_start(self):
        if self._start_time is None:
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
    Manages one streaming session using the new AWS Bedrock converse_stream API.
    
    IMPORTANT: This is now TEXT-ONLY streaming. Audio input is handled separately via
    Amazon Transcribe, then the text is streamed through this session.
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
        self.text_queue: asyncio.Queue = asyncio.Queue()
        self.tool_queue: asyncio.Queue = asyncio.Queue()
        self.transcript_queue: asyncio.Queue = asyncio.Queue()
        self.audio_queue: asyncio.Queue = asyncio.Queue()

        # State
        self.is_active = False
        self._response_task: Optional[asyncio.Task] = None
        self._content_buffer: List[str] = []
        self.latency = StreamLatencyTracker()
        self._conversation_history: List[Dict[str, Any]] = []
        self._in_thinking_block = False
        self._partial_text = ""  # For handling partial tags

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

    def _open_stream(self, messages: List[Dict[str, Any]], tool_config: Optional[Dict] = None) -> Dict[str, Any]:
        """Open a streaming request with the new API."""
        try:
            kwargs = {
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
        except Exception as e:
            raise RuntimeError(f"Bedrock streaming failed: {e}")

    async def send_audio_chunk(self, audio_data: bytes):
        """
        Process audio chunk - sends to transcript queue after STT.
        
        NOTE: Since the new API doesn't support audio input, we need to:
        1. Use Amazon Transcribe to convert audio to text
        2. Then send the text to the model
        """
        try:
            from app.services.nova_sonic import nova_sonic
            transcript = await nova_sonic._transcribe_audio_with_nova(audio_data)
            
            if transcript:
                self._conversation_history.append({"role": "user", "content": [{"text": transcript}]})
                await self.transcript_queue.put({"text": transcript})
                
                # Safety check
                if self.safety_checker:
                    safety_result = self.safety_checker(transcript)
                    if safety_result:
                        await self.transcript_queue.put({
                            "text": transcript,
                            "safety_trigger": safety_result
                        })
        except Exception as e:
            print(f"[Nova Sonic Stream] STT error: {e}")

    async def end_user_turn(self):
        """Signal end of user turn and trigger model response."""
        if not self._conversation_history:
            return
        
        await self._generate_assistant_response()

    async def _generate_assistant_response(self):
        """Generate assistant response using the conversation history."""
        try:
            # Build tool config if tools are available
            tool_config = None
            if self.tool_definitions:
                tool_config = {
                    "tools": [
                        {
                            "toolSpec": {
                                "name": tool["name"],
                                "description": tool.get("description", ""),
                                "inputSchema": tool.get("inputSchema", {})
                            }
                        }
                        for tool in self.tool_definitions
                    ]
                }
            
            # Open stream directly (boto3 converse_stream is synchronous but returns an async stream)
            stream_response = self._open_stream(self._conversation_history, tool_config)
            
            stream = stream_response['stream']
            
            # Process stream events
            for event in stream:
                if not self.is_active:
                    break

                # Text streaming
                if 'contentBlockDelta' in event:
                    delta = event['contentBlockDelta'].get('delta', {})
                    text = delta.get('text', '')
                    if text:
                        self._partial_text += text
                        
                        # Process thinking blocks - handle partial tags
                        while True:
                            # Check for opening tag (may be split across chunks)
                            if not self._in_thinking_block:
                                # Look for <thinking> tag
                                open_idx = self._partial_text.find('<thinking>')
                                if open_idx != -1:
                                    # Found opening tag
                                    before = self._partial_text[:open_idx]
                                    after = self._partial_text[open_idx + 10:]  # Skip <thinking>
                                    
                                    # Output text before the tag
                                    if before:
                                        self.latency.mark_first_chunk()
                                        await self.text_queue.put({"chunk": before})
                                    
                                    self._in_thinking_block = True
                                    self._partial_text = after
                                    continue
                                # Check for partial opening tag (<thinking)
                                elif '<thinking' in self._partial_text:
                                    # Wait for more chunks to see if it becomes <thinking>
                                    break
                            
                            # Check for closing tag (may be split)
                            if self._in_thinking_block:
                                close_idx = self._partial_text.find('</thinking>')
                                if close_idx != -1:
                                    # Found closing tag
                                    after = self._partial_text[close_idx + 12:]  # Skip </thinking>
                                    
                                    # Skip text inside thinking block
                                    self._in_thinking_block = False
                                    self._partial_text = after
                                    continue
                                # Check for partial closing tag
                                elif '</thinking' in self._partial_text or '<' in self._partial_text:
                                    # Wait for more chunks
                                    break
                            
                            # No tags found or processed, break
                            break
                        
                        # If not in thinking block and we have accumulated text with no pending tags, output it
                        if not self._in_thinking_block and self._partial_text:
                            # Only output if we're sure no opening tag is coming
                            if '<thinking' not in self._partial_text and '<' not in self._partial_text[:20]:
                                # Safe to output
                                self.latency.mark_first_chunk()
                                await self.text_queue.put({"chunk": self._partial_text})
                                self._partial_text = ""

                elif 'contentBlockStop' in event:
                    # Output any remaining text (if not in thinking block)
                    if self._partial_text and not self._in_thinking_block:
                        # Check if there's a partial opening tag
                        if '<thinking' not in self._partial_text:
                            await self.text_queue.put({"chunk": self._partial_text})
                        self._partial_text = ""
                    await self.text_queue.put({"is_last": True})

                elif 'messageStop' in event:
                    self.latency.mark_end()
                    await self.text_queue.put({"complete": True})
                    await self.text_queue.put({"turn_complete": True})

                # Tool use (if any)
                elif 'toolUseBlockStart' in event or 'toolUse' in event:
                    # Tool start detected
                    pass
                elif 'toolUseBlockDelta' in event:
                    delta = event['toolUseBlockDelta'].get('delta', {})
                    # Tool input streaming
                    pass
                elif 'toolUseBlockStop' in event:
                    # Tool completed - extract tool info from accumulated state
                    pass
                    
        except Exception as e:
            print(f"[Nova Sonic Stream] Error: {e}")
            await self.text_queue.put({"error": str(e)})

    async def send_text_message(self, message: str):
        """Send a text message directly (for text-based conversations)."""
        self._conversation_history.append({"role": "user", "content": [{"text": message}]})
        await self._generate_assistant_response()

    async def send_tool_result(self, tool_use_id: str, result: Dict[str, Any]):
        """Send tool result back to the model."""
        tool_result_content = {
            "toolResult": {
                "toolUseId": tool_use_id,
                "content": [{"text": json.dumps(result)}],
                "status": "success"
            }
        }
        
        self._conversation_history.append({
            "role": "user",
            "content": [tool_result_content]
        })
        
        await self._generate_assistant_response()

    def _loop(self):
        return asyncio.get_event_loop()

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

        # Sentinel values
        await self.text_queue.put(None)
        await self.tool_queue.put(None)
        await self.transcript_queue.put(None)
        await self.audio_queue.put(None)


def build_nova_sonic_system_prompt(
    business_context: Dict[str, Any],
    customer_context: Dict[str, Any],
    knowledge_context: str = "",
    training_context: str = "",
) -> str:
    """
    Build the system prompt for Nova Sonic voice conversations.
    
    This creates a specialized prompt optimized for voice interactions
    with the business context and customer information.
    """
    business_name = business_context.get("name", "our business")
    business_type = business_context.get("type", "general")
    services = business_context.get("services", [])
    menu = business_context.get("menu", [])
    hours = business_context.get("hours", {})
    
    customer_name = customer_context.get("name", "Unknown")
    
    prompt = f"""You are an AI voice receptionist for {business_name}, a {business_type} business.

Your role is to:
- Provide friendly, professional customer service via voice
- Answer questions about the business, services, and hours
- Help customers book appointments
- Take orders for products or services
- Transfer to a human when needed

Business Information:
- Type: {business_type}
"""
    
    if services:
        prompt += f"- Services: {', '.join(services)}\n"
    
    if menu:
        menu_items = ", ".join([f"{item.get('name', '')} (${item.get('price', 0)})" for item in menu[:10]])
        prompt += f"- Menu Items: {menu_items}\n"
    
    if hours:
        prompt += f"- Hours: {json.dumps(hours)}\n"
    
    prompt += f"""

Current Customer:
- Name: {customer_name}
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

When a customer wants to:
- Book an appointment → ask for date, time, and service
- Place an order → ask what items they want
- Get directions → provide the business address
- Speak to a human → transfer the call
"""
    
    return prompt


def build_tool_definitions(business_type: str, business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build tool definitions for Nova Sonic to use.
    
    These are the actions the AI can take during a voice conversation.
    """
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
                            "description": "The date for the appointment (e.g., 'tomorrow', 'next Tuesday', 'March 15')"
                        },
                        "time": {
                            "type": "string",
                            "description": "The time for the appointment (e.g., '2pm', '10:30 AM')"
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Customer's name"
                        },
                        "customer_phone": {
                            "type": "string",
                            "description": "Customer's phone number"
                        },
                        "service": {
                            "type": "string",
                            "description": "The type of service being booked"
                        }
                    },
                    "required": ["date", "time", "customer_name", "service"]
                }
            }
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
                            "description": "The date to check"
                        },
                        "time": {
                            "type": "string",
                            "description": "The time to check"
                        }
                    },
                    "required": ["date", "time"]
                }
            }
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
                                    "quantity": {"type": "integer"}
                                }
                            }
                        },
                        "delivery_method": {
                            "type": "string",
                            "description": "pickup or delivery"
                        }
                    }
                }
            }
        },
        {
            "name": "confirmOrder",
            "description": "Finalize and save the current order",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {}
                }
            }
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
                            "description": "Reason for transfer"
                        }
                    }
                }
            }
        },
        {
            "name": "sendDirections",
            "description": "Send directions to the business location",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {}
                }
            }
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
                            "description": "Payment amount"
                        }
                    }
                }
            }
        }
    ]
    
    return base_tools
