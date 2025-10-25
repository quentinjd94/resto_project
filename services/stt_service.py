from deepgram import DeepgramClient
from config import settings
import asyncio

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in .env!")
        
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec Deepgram
        Ultra-rapide et précis (niveau ChatGPT)
        """
        try:
            # Options de transcription
            options = {
                "model": "nova-2",
                "language": "fr",
                "smart_format": True,
                "punctuate": True,
            }
            
            # Préparer l'audio
            payload = {
                "buffer": audio_bytes,
            }
            
            # Transcription
            response = self.client.listen.rest.v("1").transcribe_file(
                payload,
                options
            )
            
            # Extraire le texte
            if response and "results" in response:
                channels = response["results"].get("channels", [])
                if channels:
                    alternatives = channels[0].get("alternatives", [])
                    if alternatives:
                        transcript = alternatives[0].get("transcript", "")
                        return transcript.strip()
            
            return ""
        
        except Exception as e:
            print(f"❌ Deepgram STT Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()