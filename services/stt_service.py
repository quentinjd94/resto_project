import httpx
from config import settings

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in .env!")
        
        self.api_key = settings.DEEPGRAM_API_KEY
        self.url = "https://api.deepgram.com/v1/listen"
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec Deepgram REST API
        """
        try:
            # Paramètres
            params = {
                "model": "nova-2",
                "language": "fr",
                "smart_format": "true",
                "punctuate": "true"
            }
            
            # Headers
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "audio/mulaw"
            }
            
            # Requête POST
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.url,
                    params=params,
                    headers=headers,
                    content=audio_bytes
                )
                
                if response.status_code != 200:
                    print(f"❌ Deepgram API error: {response.status_code} - {response.text}")
                    return ""
                
                # Parser JSON
                data = response.json()
                transcript = data['results']['channels'][0]['alternatives'][0]['transcript']
                return transcript.strip()
        
        except Exception as e:
            print(f"❌ Deepgram Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()