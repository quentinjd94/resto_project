from faster_whisper import WhisperModel
from config import settings
import io
import soundfile as sf

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
        try:
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            
            segments, info = self.model.transcribe(
                audio_data,
                language="fr",
                beam_size=5,
                vad_filter=True
            )
            
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        
        except Exception as e:
            print(f"❌ STT Error: {e}")
            return ""

stt_service = STTService()
