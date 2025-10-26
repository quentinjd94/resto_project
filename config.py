import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    #DEEPGRAM
    DEEPGRAM_API_KEY: str = ""
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    MAMA_ASSISTANT_ID: str = ""
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    
    # AssemblyAI
    ASSEMBLYAI_API_KEY: str = ""

    # Whisper
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cuda"
    
    DEEPGRAM_API_KEY: str = ""

    REDIS_URL: str = "redis://localhost:6379"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
