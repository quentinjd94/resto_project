import httpx
from config import settings
import json
from typing import AsyncGenerator

class LLMService:
    def __init__(self):
        self.url = f"{settings.OLLAMA_URL}/api/generate"
        self.model = settings.OLLAMA_MODEL
        print(f"✅ LLM ready: {self.model}")
    
    async def query_stream(self, prompt: str, system_prompt: str = None, history: list = None) -> AsyncGenerator[str, None]:
        """
        Génère la réponse token par token (streaming)
        Yield des chunks de 3-5 mots à la fois
        """
        try:
            # Construire le prompt
            full_prompt = ""
            
            if system_prompt:
                full_prompt += f"<s>[INST] {system_prompt}\n\n"
            
            if history:
                for msg in history[-2:]:  # Seulement 2 derniers pour vitesse
                    full_prompt += f"User: {msg['user']}\nAssistant: {msg['assistant']}\n\n"
            
            full_prompt += f"User: {prompt}\nAssistant: [/INST]"
            
            # Request avec stream=True
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream('POST', self.url, json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": True,  # ← STREAMING ACTIVÉ
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 100
                    }
                }) as response:
                    
                    buffer = ""
                    word_count = 0
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            
                            if token:
                                buffer += token
                                
                                # Compter les mots
                                if token.strip() and (' ' in token or '\n' in token):
                                    word_count += 1
                                
                                # Yield un chunk tous les 4-6 mots
                                if word_count >= 4:
                                    yield buffer.strip()
                                    buffer = ""
                                    word_count = 0
                            
                            # Si c'est le dernier token
                            if data.get("done", False):
                                if buffer.strip():
                                    yield buffer.strip()
                                break
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            print(f"❌ LLM Stream Error: {e}")
            yield "Désolé, je n'ai pas compris."
    
    async def query(self, prompt: str, system_prompt: str = None, history: list = None) -> str:
        """
        Version non-streaming (fallback)
        """
        full_response = ""
        async for chunk in self.query_stream(prompt, system_prompt, history):
            full_response += " " + chunk
        
        return full_response.strip()

# Instance globale
llm_service = LLMService()