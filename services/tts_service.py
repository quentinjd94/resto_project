from elevenlabs import ElevenLabs
from config import settings

class TTSService:
    def __init__(self):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not set!")
        
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        print("✅ ElevenLabs TTS ready!")
    
    async def synthesize(self, text: str) -> bytes:
        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            
            audio_bytes = b"".join(audio_generator)
            return audio_bytes
        
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return b""

tts_service = TTSService()
