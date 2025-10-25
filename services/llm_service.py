import httpx
from config import settings

class LLMService:
    def __init__(self):
        self.url = f"{settings.OLLAMA_URL}/api/generate"
        self.model = settings.OLLAMA_MODEL
        print(f"✅ LLM ready: {self.model}")
    
    async def query(self, prompt: str, system_prompt: str = None, history: list = None) -> str:
        try:
            full_prompt = ""
            
            if system_prompt:
                full_prompt += f"<s>[INST] {system_prompt}\n\n"
            
            if history:
                for msg in history:
                    full_prompt += f"User: {msg['user']}\nAssistant: {msg['assistant']}\n\n"
            
            full_prompt += f"User: {prompt}\nAssistant: [/INST]"
            
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(self.url, json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                        "num_predict": 100
                    }
                })
                
                result = response.json()
                return result.get("response", "").strip()
        
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return "Désolé, je n'ai pas compris."

llm_service = LLMService()

SYSTEM_PROMPT = """Tu es Léo, agent vocal IA pour Macadam Pizza.

RÔLE: Prendre les commandes de pizzas à emporter ou en livraison.

RÈGLES:
1. TOUJOURS demander la TAILLE (senior ou mega)
2. Confirmer chaque pizza ajoutée
3. Être chaleureux et efficace
4. Parler en français naturel

WORKFLOW:
1. Saluer: "Macadam Pizza bonsoir !"
2. Demander: emporter ou livraison ?
3. Prendre la commande
4. Récapituler
5. Annoncer délai

Réponds de manière concise et naturelle."""
