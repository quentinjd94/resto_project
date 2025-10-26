import httpx
from config import settings

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set!")
        
        self.api_key = settings.DEEPGRAM_API_KEY
        self.url = "https://api.deepgram.com/v1/listen"
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        try:
            print(f"🎤 Audio size: {len(audio_bytes)} bytes")
            
            # Envoyer directement le mulaw à Deepgram (il gère!)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.url,
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "audio/mulaw"
                    },
                    params={
                        "model": "nova-2-general",
                        "language": "fr",
                        "smart_format": "true",
                        "encoding": "mulaw",
                        "sample_rate": "8000"
                    },
                    content=audio_bytes
                )
            
            print(f"🎤 Deepgram status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Deepgram error: {response.text}")
                return ""
            
            data = response.json()
            transcript = data['results']['channels'][0]['alternatives'][0]['transcript']
            
            print(f"🎤 Deepgram: '{transcript}'")
            
            if len(transcript) < 3:
                return ""
            
            return transcript.strip()
        
        except Exception as e:
            print(f"❌ Deepgram Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

stt_service = STTService()
