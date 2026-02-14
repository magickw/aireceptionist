"""
Speech-to-Text Service using AWS Transcribe
"""

import asyncio
import json
import base64
import uuid
from typing import Optional, AsyncGenerator
import aiohttp
from app.core.config import settings


class STTService:
    """AWS Transcribe Streaming STT Service"""
    
    def __init__(self):
        self.aws_access_key = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = settings.AWS_REGION
        self.sample_rate = 8000  # Twilio uses 8kHz
        self.language_code = "en-US"
        
    async def transcribe_stream(
        self, 
        audio_chunk: bytes,
        conversation_context: Optional[dict] = None
    ) -> Optional[str]:
        """
        Transcribe a single audio chunk.
        For real-time transcription, we'd use AWS Transcribe Streaming.
        
        For now, this is a placeholder that returns None.
        Full implementation requires:
        1. AWS Transcribe Streaming SDK setup
        2. Audio format conversion (mulaw to pcm)
        3. WebSocket connection to Transcribe
        """
        # TODO: Implement full AWS Transcribe Streaming
        # For production, use amazon-transcribe-streaming-sdk
        
        # Placeholder: In a real implementation, you would:
        # 1. Convert mulaw audio to PCM
        # 2. Send to AWS Transcribe via WebSocket
        # 3. Yield transcriptions in real-time
        
        return None
    
    async def create_transcription_job(
        self,
        audio_url: str,
        job_name: Optional[str] = None
    ) -> dict:
        """
        Create an async transcription job for recorded audio.
        """
        import boto3
        
        if not self.aws_access_key or not self.aws_secret_key:
            return {"error": "AWS credentials not configured"}
        
        try:
            transcribe = boto3.client(
                'transcribe',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            job_name = job_name or f"receptionist_{uuid.uuid4().hex[:8]}"
            
            response = transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_url},
                MediaFormat='wav',
                LanguageCode=self.language_code,
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 10
                }
            )
            
            return {
                "job_name": job_name,
                "status": response['TranscriptionJob']['TranscriptionJobStatus']
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_transcription_result(self, job_name: str) -> dict:
        """
        Get the result of a transcription job.
        """
        import boto3
        
        if not self.aws_access_key or not self.aws_secret_key:
            return {"error": "AWS credentials not configured"}
        
        try:
            transcribe = boto3.client(
                'transcribe',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            response = transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            job = response['TranscriptionJob']
            
            if job['TranscriptionJobStatus'] == 'COMPLETED':
                # Fetch the actual transcript
                import urllib.request
                import json
                
                transcript_uri = job['Transcript']['TranscriptFileUri']
                with urllib.request.urlopen(transcript_uri) as url:
                    transcript_data = json.loads(url.read().decode())
                    return {
                        "status": "completed",
                        "transcript": transcript_data['results']['transcripts'][0]['transcript'],
                        "items": transcript_data['results']['items']
                    }
            else:
                return {
                    "status": job['TranscriptionJobStatus'],
                    "failure_reason": job.get('FailureReason', None)
                }
                
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
stt_service = STTService()
