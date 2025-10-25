from deepgram import DeepgramClient
from config import settings

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in .env!")
        
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec Deepgram
        """
        try:
            # Utiliser la méthode synchrone puis async wrapper
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                {"buffer": audio_bytes},
                {
                    "model": "nova-2",
                    "language": "fr",
                    "smart_format": True,
                }
            )
            
            # Parser la réponse
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript.strip()
        
        except Exception as e:
            print(f"❌ Deepgram Error: {e}")
            return ""

# Instance globale
stt_service = STTService()