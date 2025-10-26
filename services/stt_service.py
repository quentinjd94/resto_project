from openai import OpenAI
from config import settings
import tempfile
import os
import wave
import audioop

class STTService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set!")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("✅ OpenAI Whisper ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit avec Whisper API
        """
        try:
            print(f"🎤 Audio size: {len(audio_bytes)} bytes")
        
            # Convertir mulaw → WAV
            pcm_data = audioop.ulaw2lin(audio_bytes, 2)
            pcm_16k, _ = audioop.ratecv(pcm_data, 2, 1, 8000, 16000, None)
        
            print(f"🎤 PCM size: {len(pcm_16k)} bytes")
        
            # Créer WAV temporaire
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                with wave.open(tmp.name, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(pcm_16k)
                tmp_path = tmp.name
        
            try:
                # Transcription Whisper API
                with open(tmp_path, 'rb') as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="fr",
                        prompt="Commande de restaurant, poke bowl, sushi"  # ← Aide le contexte
                    )
            
                result = transcript.text.strip()
                print(f"🎤 Transcription: '{result}'")
            
                # Filtrer les parasites
                if "sous-titr" in result.lower() or len(result) < 3:
                    print(f"⚠️ Transcription rejetée (parasite)")
                    return ""
            
                return result
            finally:
                os.unlink(tmp_path)
    
        except Exception as e:
            print(f"❌ Whisper API Error: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
stt_service = STTService()
