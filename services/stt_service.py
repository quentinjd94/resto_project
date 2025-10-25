from elevenlabs import ElevenLabs
from config import settings
import subprocess
import tempfile
import os

class TTSService:
    def __init__(self):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not set!")
        
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        print("✅ ElevenLabs TTS ready!")
    
    async def synthesize(self, text: str) -> bytes:
        """
        Convertit texte → audio mulaw pour Twilio
        """
        try:
            # 1. Générer audio MP3 avec ElevenLabs
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            
            # Collecter tous les chunks MP3
            mp3_data = b"".join(audio_generator)
            
            # 2. Convertir MP3 → mulaw 8kHz pour Twilio
            # Utiliser ffmpeg via fichiers temporaires
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
                mp3_file.write(mp3_data)
                mp3_path = mp3_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.ulaw', delete=False) as mulaw_file:
                mulaw_path = mulaw_file.name
            
            try:
                # Convertir avec ffmpeg: MP3 → mulaw 8kHz mono
                subprocess.run([
                    'ffmpeg',
                    '-i', mp3_path,
                    '-ar', '8000',      # Sample rate 8kHz
                    '-ac', '1',         # Mono
                    '-f', 'mulaw',      # Format mulaw
                    '-y',               # Overwrite
                    mulaw_path
                ], check=True, capture_output=True)
                
                # Lire le fichier mulaw
                with open(mulaw_path, 'rb') as f:
                    mulaw_data = f.read()
                
                return mulaw_data
            
            finally:
                # Nettoyer les fichiers temporaires
                os.unlink(mp3_path)
                os.unlink(mulaw_path)
        
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            import traceback
            traceback.print_exc()
            return b""

# Instance globale
tts_service = TTSService()
