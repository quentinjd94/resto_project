from deepgram import DeepgramClient
from config import settings

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in .env!")
        
        # Initialiser avec config dict
        self.client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec Deepgram
        """
        try:
            # Options en dict pur
            options = {
                "model": "nova-2",
                "language": "fr",
                "smart_format": True,
                "punctuate": True
            }
            
            # Source
            source = {"buffer": audio_bytes}
            
            # Transcription
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                source, options
            )
            
            # Parser la réponse (peut être un dict ou un objet)
            if hasattr(response, 'results'):
                # C'est un objet
                transcript = response.results.channels[0].alternatives[0].transcript
            else:
                # C'est un dict
                transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
            
            return transcript.strip()
        
        except Exception as e:
            print(f"❌ Deepgram Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()