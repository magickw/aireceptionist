"""
Nova 2 Sonic Speech-to-Speech Handler
Autonomous Business Operations Agent - Voice Layer
"""
import boto3
import json
import base64
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from app.core.config import settings


class NovaSonicHandler:
    """
    Nova 2 Sonic-powered speech-to-speech handler with bidirectional streaming.
    
    Provides:
    - Real-time speech-to-speech processing
    - Low-latency conversational audio
    - Streaming transcripts for UI
    - Optimized for natural dialogue flow
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = "amazon.nova-sonic-v1:0"
        
        # Audio configuration
        self.sample_rate = 16000  # 16kHz for voice
        self.channels = 1  # Mono
        self.bit_depth = 16  # PCM16
        self.audio_format = "pcm16"
        
        # Latency optimization settings
        self.max_response_duration = 30000  # 30 seconds max response
        self.temperature = 0.7  # Natural speaking variation
        self.top_p = 0.9
        
        # Buffer management
        self.input_buffer: list[bytes] = []
        self.output_buffer: list[bytes] = []
        self.is_processing = False
    
    async def process_audio_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process incoming audio stream and generate speech-to-speech responses.
        
        Args:
            audio_stream: Async generator of audio chunks (PCM16 bytes)
            conversation_context: Context about the conversation (history, customer info, etc.)
            
        Yields:
            Dictionaries with response data:
            - {"type": "transcript", "text": "..."}
            - {"type": "audio", "data": bytes}
            - {"type": "reasoning", "data": {...}}
            - {"type": "complete", "transcript": "..."}
        """
        try:
            # Collect audio chunks
            audio_chunks = []
            async for chunk in audio_stream:
                audio_chunks.append(chunk)
            
            # Combine chunks for processing
            if not audio_chunks:
                yield {
                    "type": "error",
                    "message": "No audio data received"
                }
                return
            
            combined_audio = b''.join(audio_chunks)
            
            # Process through Nova Sonic
            async for response in self._invoke_nova_sonic_stream(
                combined_audio,
                conversation_context
            ):
                yield response
                
        except Exception as e:
            yield {
                "type": "error",
                "message": f"Audio processing error: {str(e)}"
            }
    
    async def _invoke_nova_sonic_stream(
        self,
        audio_data: bytes,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Invoke Nova 2 Sonic with streaming response.
        
        This is a placeholder implementation. The actual Nova 2 Sonic API
        will be updated by AWS to support streaming speech-to-speech.
        
        For now, we use a hybrid approach:
        1. Transcribe audio (using Transcribe or similar)
        2. Get text response (using Nova Lite)
        3. Synthesize speech (using Polly or Nova TTS)
        """
        
        # Step 1: Transcribe audio to text
        transcript = await self._transcribe_audio(audio_data)
        
        if not transcript:
            yield {
                "type": "error",
                "message": "Could not transcribe audio"
            }
            return
        
        yield {
            "type": "transcript",
            "text": transcript
        }
        
        # Step 2: Get text response (this will be integrated with Nova Lite reasoning)
        text_response = await self._get_text_response(transcript, context)
        
        yield {
            "type": "text_response",
            "text": text_response
        }
        
        # Step 3: Synthesize speech
        audio_response = await self._synthesize_speech(text_response)
        
        if audio_response:
            yield {
                "type": "audio",
                "data": audio_response
            }
        
        yield {
            "type": "complete",
            "transcript": transcript,
            "response": text_response
        }
    
    async def _transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio to text.
        
        In production, this would use Amazon Transcribe Streaming API.
        For now, we'll use a mock implementation.
        """
        # TODO: Integrate Amazon Transcribe Streaming
        # For demo purposes, return a mock transcript
        return "I would like to book an appointment for tomorrow."
    
    async def _get_text_response(
        self,
        transcript: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get text response from Nova Lite reasoning engine.
        
        This will integrate with the nova_reasoning.py service.
        """
        # Import here to avoid circular dependency
        from app.services.nova_reasoning import nova_reasoning
        
        business_context = context.get("business_context", {}) if context else {}
        customer_context = context.get("customer_context", {}) if context else {}
        
        try:
            reasoning_result = await nova_reasoning.reason(
                conversation=transcript,
                business_context=business_context,
                customer_context=customer_context
            )
            
            return reasoning_result.get("suggested_response", "I'm here to help you.")
            
        except Exception as e:
            # Fallback response
            return "I understand you'd like to book an appointment. Let me help you with that."
    
    async def _synthesize_speech(self, text: str) -> Optional[bytes]:
        """
        Synthesize text to speech using Polly or Nova TTS.
        
        Returns PCM16 audio bytes at 16kHz.
        """
        try:
            polly = boto3.client(
                service_name='polly',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='pcm',
                VoiceId='Joanna',  # Neural voice for natural sound
                SampleRate='16000',
                Engine='neural'
            )
            
            # Read the audio stream
            audio_data = response['AudioStream'].read()
            
            return audio_data
            
        except Exception as e:
            print(f"Speech synthesis error: {e}")
            return None
    
    async def process_text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech (for non-voice interactions).
        
        Args:
            text: Text to synthesize
            
        Returns:
            PCM16 audio bytes at 16kHz
        """
        return await self._synthesize_speech(text)
    
    def get_audio_config(self) -> Dict[str, Any]:
        """
        Get audio configuration for the client.
        
        Returns configuration that the client should use for recording/playback.
        """
        return {
            "sampleRate": self.sample_rate,
            "channels": self.channels,
            "bitDepth": self.bit_depth,
            "format": self.audio_format,
            "mimeType": "audio/pcm",
            "maxChunkSize": 4096,  # Recommended chunk size
            "targetLatency": 150  # Target latency in ms
        }
    
    def encode_audio_base64(self, audio_data: bytes) -> str:
        """
        Encode audio data to base64 for WebSocket transmission.
        """
        return base64.b64encode(audio_data).decode('utf-8')
    
    def decode_audio_base64(self, base64_data: str) -> bytes:
        """
        Decode base64 audio data.
        """
        return base64.b64decode(base64_data)


# Singleton instance
nova_sonic = NovaSonicHandler()


class AudioBuffer:
    """
    Audio buffer for managing streaming audio data.
    """
    
    def __init__(self, max_size: int = 1024 * 1024):  # 1MB default
        self.buffer: list[bytes] = []
        self.max_size = max_size
        self.current_size = 0
    
    def add(self, chunk: bytes) -> bool:
        """Add audio chunk to buffer. Returns False if buffer is full."""
        chunk_size = len(chunk)
        
        if self.current_size + chunk_size > self.max_size:
            return False
        
        self.buffer.append(chunk)
        self.current_size += chunk_size
        return True
    
    def get_all(self) -> bytes:
        """Get all buffered audio data."""
        combined = b''.join(self.buffer)
        self.clear()
        return combined
    
    def clear(self):
        """Clear the buffer."""
        self.buffer = []
        self.current_size = 0
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0
    
    def size(self) -> int:
        """Get current buffer size."""
        return self.current_size


class LatencyTracker:
    """
    Track audio processing latency for optimization.
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.transcription_time: Optional[float] = None
        self.reasoning_time: Optional[float] = None
        self.synthesis_time: Optional[float] = None
    
    def start(self):
        """Start tracking."""
        import time
        self.start_time = time.time()
    
    def mark_transcription(self):
        """Mark transcription completion."""
        import time
        self.transcription_time = time.time()
    
    def mark_reasoning(self):
        """Mark reasoning completion."""
        import time
        self.reasoning_time = time.time()
    
    def mark_synthesis(self):
        """Mark synthesis completion."""
        import time
        self.synthesis_time = time.time()
    
    def end(self):
        """End tracking."""
        import time
        self.end_time = time.time()
    
    def get_metrics(self) -> Dict[str, float]:
        """Get latency metrics in milliseconds."""
        if not self.start_time or not self.end_time:
            return {}
        
        total_latency = (self.end_time - self.start_time) * 1000
        
        metrics = {
            "total_latency_ms": round(total_latency, 2)
        }
        
        if self.transcription_time:
            metrics["transcription_latency_ms"] = round(
                (self.transcription_time - self.start_time) * 1000, 2
            )
        
        if self.reasoning_time:
            metrics["reasoning_latency_ms"] = round(
                (self.reasoning_time - self.transcription_time) * 1000, 2
            ) if self.transcription_time else 0
        
        if self.synthesis_time:
            metrics["synthesis_latency_ms"] = round(
                (self.synthesis_time - self.reasoning_time) * 1000, 2
            ) if self.reasoning_time else 0
        
        return metrics
    
    def reset(self):
        """Reset the tracker."""
        self.start_time = None
        self.end_time = None
        self.transcription_time = None
        self.reasoning_time = None
        self.synthesis_time = None