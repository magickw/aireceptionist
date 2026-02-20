from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Receptionist Pro"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # Google Calendar Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "https://receptium.onrender.com/api/calendar/google/callback"
    
    # Microsoft Calendar Configuration
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "https://receptium.onrender.com/api/calendar/microsoft/callback"
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS: Optional[str] = None

    # Stripe Configuration
    STRIPE_SECRET_KEY: Optional[str] = None

    # Nova Sonic Streaming Configuration
    NOVA_SONIC_STREAMING_ENABLED: bool = True
    NOVA_SONIC_VOICE_ID: str = "matthew"
    NOVA_SONIC_OUTPUT_SAMPLE_RATE: int = 24000
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
