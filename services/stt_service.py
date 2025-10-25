import assemblyai as aai
from config import settings
import tempfile
import os

class STTService:
    def __init__(self):
        if not settings.ASSEMBLYAI_API_KEY:
            raise ValueError("ASSEMBLYAI_API_KEY not set in .env!")
        
        # Configurer AssemblyAI
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        
        # Config de transcription
        self.config = aai.TranscriptionConfig(
            language_code="fr",  # Français
            punctuate=True,
            format_text=True,
            speech_model=aai.SpeechModel.best  # Meilleur modèle
        )
        
        print("✅ AssemblyAI STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec AssemblyAI
        Qualité ChatGPT niveau
        """
        try:
            # AssemblyAI nécessite un fichier temporaire
            with tempfile.NamedTemporaryFile(suffix='.mulaw', delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            try:
                # Transcription
                transcriber = aai.Transcriber(config=self.config)
                transcript = transcriber.transcribe(tmp_path)
                
                # Vérifier le statut
                if transcript.status == aai.TranscriptStatus.error:
                    print(f"❌ AssemblyAI Error: {transcript.error}")
                    return ""
                
                # Retourner le texte
                return transcript.text.strip() if transcript.text else ""
            
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            print(f"❌ AssemblyAI Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()