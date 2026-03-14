from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Receptionist Pro"
    API_V1_STR: str = "/api"
    
    # Application base URL (used for webhooks, callbacks, etc.)
    APP_BASE_URL: Optional[str] = None

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_RATE_LIMIT_PER_SECOND: int = 10  # Max Twilio API calls per second

    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # Refresh Tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google Calendar Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "https://receptium.onrender.com/api/calendar/google/callback"

    # Microsoft Calendar Configuration
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "https://receptium.onrender.com/api/calendar/microsoft/callback"

    # Calendly Configuration
    CALENDLY_CLIENT_ID: Optional[str] = None
    CALENDLY_CLIENT_SECRET: Optional[str] = None
    CALENDLY_REDIRECT_URI: str = "https://receptium.onrender.com/api/calendly/callback"
    CALENDLY_WEBHOOK_SECRET: Optional[str] = None

    # Firebase Configuration
    FIREBASE_CREDENTIALS: Optional[str] = None

    # Stripe Configuration
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Nova Sonic Streaming Configuration
    NOVA_SONIC_STREAMING_ENABLED: bool = True
    NOVA_SONIC_VOICE_ID: str = "matthew"
    NOVA_SONIC_OUTPUT_SAMPLE_RATE: int = 24000

    # AWS Bedrock Model Configuration (configurable for A/B testing, model upgrades)
    BEDROCK_REASONING_MODEL: str = "amazon.nova-lite-v1:0"  # For general reasoning and responses
    BEDROCK_VOICE_MODEL: str = "amazon.nova-sonic-v1:0"     # For real-time voice conversations
    BEDROCK_AUTOMATION_MODEL: str = "amazon.nova-act-v1:0"  # For browser automation
    BEDROCK_EMBEDDING_MODEL: str = "amazon.titan-embed-text-v1"  # For vector embeddings
    
    # Model fallback chain (comma-separated list of model IDs)
    BEDROCK_REASONING_FALLBACK_MODELS: str = ""  # e.g., "anthropic.claude-3-sonnet,anthropic.claude-3-haiku"

    # E4: Voice Latency Optimization
    STREAMING_STT_ENABLED: bool = True  # Streaming STT via Amazon Transcribe (no S3 needed)
    INCREMENTAL_TTS_ENABLED: bool = True  # Sentence-level TTS for lower latency
    TTS_MIN_SENTENCE_LENGTH: int = 20  # Minimum chars before synthesizing a sentence

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
