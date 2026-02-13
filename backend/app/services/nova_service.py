import boto3
import json
import base64
from app.core.config import settings

class NovaService:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.transcribe = boto3.client(
            service_name='transcribe',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.polly = boto3.client(
            service_name='polly',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        # Using Amazon Nova Lite (or similar performant model)
        self.model_id = "amazon.nova-lite-v1:0" 

    async def transcribe_audio(self, audio_bytes):
        # In a real streaming setup, we'd use Transcribe Streaming.
        # For this prototype, we might simulate or use a quick synchronous call if chunks are large enough,
        # but realistically we need a streaming client.
        # For simplicity in this CLI context, I will mock the STT part or assume text input for now 
        # to focus on the Agent logic, OR implemented a basic wrapper.
        pass

    def generate_response(self, messages, tools=None):
        """
        Invokes Nova Lite for reasoning.
        """
        body = {
            "inferenceConfig": {
                "max_new_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9,
            },
            "messages": messages
        }
        
        # Add system prompt if needed (Nova uses 'system' role in messages usually, 
        # or a separate field depending on specific API version).
        # Checking Bedrock Converse API structure.
        
        response = self.bedrock_runtime.converse(
            modelId=self.model_id,
            messages=messages,
            system=[{"text": "You are an AI receptionist. Be polite, concise, and helpful."}],
            inferenceConfig={"temperature": 0.5}
        )
        
        return response['output']['message']

    def text_to_speech(self, text):
        response = self.polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        return response['AudioStream'].read()

nova_service = NovaService()
