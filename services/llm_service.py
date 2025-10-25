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
        """
        try:
            # Construire le prompt pour Mistral Instruct
            messages = []
            
            # System prompt
            if system_prompt:
                messages.append(f"[INST] {system_prompt} [/INST]")
            
            # History
            if history:
                for msg in history[-2:]:
                    messages.append(f"[INST] {msg['user']} [/INST] {msg['assistant']}")
            
            # Current prompt
            messages.append(f"[INST] {prompt} [/INST]")
            
            full_prompt = "\n".join(messages)
            
            # Request avec stream=True
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream('POST', self.url, json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 150,
                        "stop": ["[INST]", "</s>"]
                    }
                }) as response:
                    
                    buffer = ""
                    word_buffer = ""
                    word_count = 0
                    
                    # Lire byte par byte et parser les lignes JSON
                    async for chunk in response.aiter_bytes():
                        text = chunk.decode('utf-8')
                        
                        for char in text:
                            if char == '\n':
                                # On a une ligne complète JSON
                                if buffer.strip():
                                    try:
                                        data = json.loads(buffer)
                                        token = data.get("response", "")
                                        
                                        if token:
                                            word_buffer += token
                                            
                                            # Yield tous les 4-6 mots ou à chaque ponctuation forte
                                            if token in ['.', '!', '?', '\n']:
                                                if word_buffer.strip():
                                                    yield word_buffer.strip()
                                                    word_buffer = ""
                                                    word_count = 0
                                            elif ' ' in token:
                                                word_count += 1
                                                if word_count >= 5:
                                                    if word_buffer.strip():
                                                        yield word_buffer.strip()
                                                        word_buffer = ""
                                                        word_count = 0
                                        
                                        # Si done, yield le reste
                                        if data.get("done", False):
                                            if word_buffer.strip():
                                                yield word_buffer.strip()
                                            return
                                    
                                    except json.JSONDecodeError:
                                        pass
                                
                                buffer = ""
                            else:
                                buffer += char
        
        except Exception as e:
            print(f"❌ LLM Stream Error: {e}")
            import traceback
            traceback.print_exc()
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