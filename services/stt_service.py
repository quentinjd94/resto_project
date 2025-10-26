import httpx
from config import settings
import tempfile
import os
import wave
import audioop

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set!")
        
        self.api_key = settings.DEEPGRAM_API_KEY
        self.url = "https://api.deepgram.com/v1/listen"
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        try:
            # Convertir mulaw → WAV
            pcm_data = audioop.ulaw2lin(audio_bytes, 2)
            pcm_16k, _ = audioop.ratecv(pcm_data, 2, 1, 8000, 16000, None)
            
            # WAV temporaire
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                with wave.open(tmp.name, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(pcm_16k)
                tmp_path = tmp.name
            
            try:
                # Deepgram API
                async with httpx.AsyncClient(timeout=10.0) as client:
                    with open(tmp_path, 'rb') as audio_file:
                        response = await client.post(
                            self.url,
                            headers={
                                "Authorization": f"Token {self.api_key}",
                                "Content-Type": "audio/wav"
                            },
                            params={
                                "model": "nova-2-phonecall",
                                "language": "fr",
                                "smart_format": "true",
                                "punctuate": "true"
                            },
                            content=audio_file.read()
                        )
                
                if response.status_code != 200:
                    print(f"❌ Deepgram: {response.status_code}")
                    return ""
                
                data = response.json()
                transcript = data['results']['channels'][0]['alternatives'][0]['transcript']
                
                print(f"🎤 Deepgram: '{transcript}'")
                
                if len(transcript) < 3:
                    return ""
                
                return transcript.strip()
            finally:
                os.unlink(tmp_path)
        
        except Exception as e:
            print(f"❌ Deepgram Error: {e}")
            return ""

stt_service = STTService()
