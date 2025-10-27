from openai import OpenAI
from config import settings
from typing import AsyncGenerator, Tuple, Optional
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
        thread_id: Optional[str] = None,
        history: list = None
    ) -> AsyncGenerator[Tuple[str, str], None]:
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
            
                # IMPORTANT: Vérifier qu'il n'y a pas de run actif
                runs = self.client.beta.threads.runs.list(thread_id=thread_id, limit=1)
                if runs.data:
                    last_run = runs.data[0]
                    if last_run.status in ['queued', 'in_progress', 'requires_action']:
                        print(f"⚠️ Run encore actif ({last_run.status}), on attend...")
                        # Attendre que le run se termine
                        import time
                        max_wait = 5  # secondes
                        waited = 0
                        while last_run.status in ['queued', 'in_progress'] and waited < max_wait:
                            time.sleep(0.5)
                            waited += 0.5
                            last_run = self.client.beta.threads.runs.retrieve(
                                thread_id=thread_id,
                                run_id=last_run.id
                            )
                            print(f"⏳ Run status: {last_run.status}")
                    
                        if last_run.status in ['queued', 'in_progress']:
                            print(f"⚠️ Run toujours actif après {max_wait}s, création nouveau thread")
                            thread = self.client.beta.threads.create()
                            thread_id = thread.id
        
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
                                            yield (buffer.strip(), thread_id)
                                            buffer = ""
                                            word_count = 0
                
                    # Function calls
                    elif event.event == 'thread.run.requires_action':
                        # Récupérer les tool calls demandés
                        run_id = event.data.id
                        tool_calls = event.data.required_action.submit_tool_outputs.tool_calls
    
                        print(f"⚙️ Functions demandées: {[tc.function.name for tc in tool_calls]}")
    
                        # Pour l'instant, yield juste le signal
                        for tool_call in tool_calls:
                            yield ("[FUNCTION_CALL]", thread_id)
            
                # Yield reste
                if buffer.strip():
                    yield (buffer.strip(), thread_id)
    
        except Exception as e:
            print(f"❌ Assistant Error: {e}")
            import traceback
            traceback.print_exc()
            yield ("Désolé, problème technique.", thread_id if thread_id else "")

llm_service = LLMService()
