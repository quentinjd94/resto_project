from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from config import settings
import asyncio

class STTService:
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in .env!")
        
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        print("✅ Deepgram STT ready!")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcrit audio mulaw → texte français avec Deepgram
        Ultra-rapide et précis (niveau ChatGPT)
        """
        try:
            # Deepgram accepte directement le mulaw
            # Pas besoin de conversion !
            
            # Options de transcription
            options = PrerecordedOptions(
                model="nova-2",  # Modèle le plus récent et précis
                language="fr",   # Français
                smart_format=True,  # Ponctuation automatique
                punctuate=True,
                diarize=False,  # Pas besoin de distinguer les speakers
                utterances=False
            )
            
            # Préparer l'audio
            payload: FileSource = {
                "buffer": audio_bytes,
            }
            
            # Transcription (async)
            response = await asyncio.to_thread(
                self.client.listen.prerecorded.v("1").transcribe_file,
                payload,
                options
            )
            
            # Extraire le texte
            if response.results and response.results.channels:
                transcript = response.results.channels[0].alternatives[0].transcript
                return transcript.strip()
            
            return ""
        
        except Exception as e:
            print(f"❌ Deepgram STT Error: {e}")
            import traceback
            traceback.print_exc()
            return ""

# Instance globale
stt_service = STTService()