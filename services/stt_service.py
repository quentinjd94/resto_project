from openai import OpenAI
from config import settings
import tempfile
import os
import wave
import audioop
import webrtcvad

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
            # Convertir mulaw → WAV
            pcm_data = audioop.ulaw2lin(audio_bytes, 2)
            pcm_16k, _ = audioop.ratecv(pcm_data, 2, 1, 8000, 16000, None)

            # VAD - Vérifier si c'est de la vraie voix
            vad = webrtcvad.Vad(3)  # Agressivité max
        
            # Découper en frames de 30ms
            frame_duration = 30  # ms
            frame_size = int(16000 * frame_duration / 1000) * 2  # bytes
        
            frames_with_voice = 0
            total_frames = 0
        
            for i in range(0, len(pcm_16k) - frame_size, frame_size):
                frame = pcm_16k[i:i + frame_size]
                if len(frame) == frame_size:
                    total_frames += 1
                    try:
                        if vad.is_speech(frame, 16000):
                            frames_with_voice += 1
                    except:
                        pass
        
            # Si moins de 30% de voix → rejeter
            if total_frames > 0:
                voice_ratio = frames_with_voice / total_frames
                print(f"🎤 Voice ratio: {voice_ratio:.2%}")
            
                if voice_ratio < 0.3:
                    print(f"⚠️ Pas assez de voix détectée, rejeté")
                    return ""
            
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
                        prompt="Commande restaurant poke bowl sushi"
                    )
                
                result = transcript.text.strip()
                print(f"🎤 Transcription brute: '{result}'")
                
                # FILTRES ANTI-PARASITES
                parasites = [
                    "sous-titr",
                    "youtube",
                    "abonner",
                    "vidéo",
                    "chaîne",
                    "pokemonday",
                    "merci d'avoir regardé",
                    "à la prochaine"
                ]
                
                # Si contient un parasite → rejeter
                if any(p in result.lower() for p in parasites):
                    print(f"⚠️ Parasite détecté, rejeté")
                    return ""
                
                # Si trop long
                if len(result) > 100:
                    print(f"⚠️ Texte trop long, rejeté")
                    return ""
                
                # Si trop court
                if len(result) < 3:
                    print(f"⚠️ Texte trop court, rejeté")
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
