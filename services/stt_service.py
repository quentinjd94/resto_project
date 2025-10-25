from faster_whisper import WhisperModel
from config import settings
import io
import numpy as np
import wave
import audioop

class STTService:
    def __init__(self):
        print(f"Loading Whisper {settings.WHISPER_MODEL}...")
        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type="float16"
        )
        print("✅ Whisper loaded!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio bytes → texte français
        Twilio envoie en mulaw 8kHz, on doit convertir en PCM 16kHz
        """
        try:
            # Twilio envoie en mulaw 8000 Hz mono
            # On doit convertir en PCM linéaire
            
            # 1. Convertir mulaw → PCM linéaire 16-bit
            pcm_data = audioop.ulaw2lin(audio_bytes, 2)  # 2 = 16-bit samples
            
            # 2. Resample 8kHz → 16kHz (Whisper préfère 16kHz)
            pcm_16k, _ = audioop.ratecv(
                pcm_data,
                2,      # sample width (16-bit)
                1,      # channels (mono)
                8000,   # input rate
                16000,  # output rate (16kHz)
                None
            )
            
            # 3. Convertir en numpy array float32 normalisé
            audio_np = np.frombuffer(pcm_16k, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 4. Transcription avec Whisper
            segments, info = self.model.transcribe(
                audio_np,
                language="fr",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # 5. Joindre tous les segments
            text = " ".join([segment.text for segment in segments])
            
            return text.strip()
        
        except Exception as e:
            print(f"❌ STT Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()
