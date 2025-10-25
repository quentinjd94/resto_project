from deepgram import DeepgramClient
from config import settings

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in .env!")
        
        self.client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec Deepgram
        """
        try:
            # Options
            options = {
                "model": "nova-2",
                "language": "fr",
                "smart_format": True,
                "punctuate": True
            }
            
            # Source
            source = {"buffer": audio_bytes}
            
            # Transcription avec la bonne syntaxe: .v1() ou .v2()
            response = self.client.listen.v1().transcribe_file(
                source, options
            )
            
            # Parser la réponse
            if hasattr(response, 'results'):
                transcript = response.results.channels[0].alternatives[0].transcript
            else:
                transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
            
            return transcript.strip()
        
        except Exception as e:
            print(f"❌ Deepgram Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()