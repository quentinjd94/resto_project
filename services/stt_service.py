import assemblyai as aai
from config import settings
import tempfile
import os
import wave
import audioop

class STTService:
    def __init__(self):
        if not settings.ASSEMBLYAI_API_KEY:
            raise ValueError("ASSEMBLYAI_API_KEY not set in .env!")
        
        # Configurer AssemblyAI
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        
        # Config de transcription
        self.config = aai.TranscriptionConfig(
            language_code="fr",
            punctuate=True,
            format_text=True,
            speech_model=aai.SpeechModel.best
        )
        
        print("✅ AssemblyAI STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec AssemblyAI
        """
        try:
            # 1. Convertir mulaw → PCM linéaire 16-bit
            pcm_data = audioop.ulaw2lin(audio_bytes, 2)
            
            # 2. Resample 8kHz → 16kHz (AssemblyAI préfère 16kHz+)
            pcm_16k, _ = audioop.ratecv(
                pcm_data,
                2,      # 16-bit
                1,      # mono
                8000,   # input rate
                16000,  # output rate
                None
            )
            
            # 3. Créer un fichier WAV temporaire
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
                
                with wave.open(tmp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)        # Mono
                    wav_file.setsampwidth(2)        # 16-bit
                    wav_file.setframerate(16000)    # 16kHz
                    wav_file.writeframes(pcm_16k)
            
            try:
                # 4. Transcription
                transcriber = aai.Transcriber(config=self.config)
                transcript = transcriber.transcribe(tmp_path)
                
                # Vérifier le statut
                if transcript.status == aai.TranscriptStatus.error:
                    print(f"❌ AssemblyAI Error: {transcript.error}")
                    return ""
                
                # Retourner le texte
                text = transcript.text.strip() if transcript.text else ""
                return text
            
            finally:
                # Nettoyer
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            print(f"❌ AssemblyAI Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()