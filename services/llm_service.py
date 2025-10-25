from openai import OpenAI
from config import settings
from typing import AsyncGenerator

class LLMService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set!")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("✅ OpenAI GPT-4o-mini ready!")
    
    async def query_stream(self, prompt: str, system_prompt: str = None, history: list = None) -> AsyncGenerator[str, None]:
        """
        Génère réponse avec GPT-4o-mini STREAMING
        """
        try:
            messages = []
            
            # System
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # History
            if history:
                for msg in history[-3:]:
                    messages.append({"role": "user", "content": msg['user']})
                    messages.append({"role": "assistant", "content": msg['assistant']})
            
            # Current
            messages.append({"role": "user", "content": prompt})
            
            # Streaming
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stream=True
            )
            
            buffer = ""
            word_count = 0
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    buffer += token
                    
                    # Yield tous les 5 mots
                    if ' ' in token or token in ['.', '!', '?']:
                        word_count += 1
                        if word_count >= 5 or token in ['.', '!', '?']:
                            if buffer.strip():
                                yield buffer.strip()
                                buffer = ""
                                word_count = 0
            
            # Yield reste
            if buffer.strip():
                yield buffer.strip()
        
        except Exception as e:
            print(f"❌ GPT Error: {e}")
            yield "Désolé, service indisponible."
    
    async def query(self, prompt: str, system_prompt: str = None, history: list = None) -> str:
        full = ""
        async for chunk in self.query_stream(prompt, system_prompt, history):
            full += " " + chunk
        return full.strip()

llm_service = LLMService()