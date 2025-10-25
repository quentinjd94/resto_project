import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:7b-instruct-q5_K_M"
    OLLAMA_TIMEOUT: int = 30
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    
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
