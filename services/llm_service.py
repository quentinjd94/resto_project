from openai import OpenAI
from config import settings
from typing import AsyncGenerator
import json
from datetime import datetime

class LLMService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set!")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("✅ OpenAI with Assistants API ready!")
    
    async def query_stream(
        self, 
        prompt: str, 
        restaurant_id: str,
        assistant_id: str,
        thread_id: str = None,
        history: list = None
    ) -> AsyncGenerator[tuple, None]:  # ← Retourne (chunk, thread_id)
        """
        Utilise OpenAI Assistants API avec streaming
        """
        try:
            # Créer ou réutiliser thread
            if not thread_id:
                thread = self.client.beta.threads.create()
                thread_id = thread.id
                print(f"🧵 Thread créé: {thread_id}")
            else:
                print(f"🧵 Thread réutilisé: {thread_id}")
        
            # Ajouter le message user
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
        
            # Run avec streaming
            with self.client.beta.threads.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
            ) as stream:
            
                buffer = ""
                word_count = 0
            
                for event in stream:
                    # Text delta
                    if event.event == 'thread.message.delta':
                        for content in event.data.delta.content:
                            if content.type == 'text':
                                token = content.text.value
                                buffer += token
                            
                                # Yield tous les 5 mots ou ponctuation
                                if ' ' in token or token in ['.', '!', '?', '\n']:
                                    word_count += 1
                                    if word_count >= 5 or token in ['.', '!', '?']:
                                        if buffer.strip():
                                            yield (buffer.strip(), thread_id)  # ← Yield tuple
                                            buffer = ""
                                            word_count = 0
                
                    # Function calls
                    elif event.event == 'thread.run.requires_action':
                        yield ("[FUNCTION_CALL]", thread_id)
            
                # Yield reste
                if buffer.strip():
                    yield (buffer.strip(), thread_id)
    
        except Exception as e:
            print(f"❌ Assistant Error: {e}")
            import traceback
            traceback.print_exc()
            yield ("Désolé, problème technique.", thread_id if thread_id else None)
            
llm_service = LLMService()
