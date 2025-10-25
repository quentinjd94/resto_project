from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn
import json
from datetime import datetime
import asyncio
import base64

from config import settings
from database import db
from services import stt_service, tts_service, llm_service
from utils.prompt_builder import build_dynamic_prompt

app = FastAPI(title="Pizza Agent AI - Multi Restaurant")

# Store active calls
active_calls = {}

@app.get("/")
async def root():
    return {"status": "ok", "service": "pizza-agent-ai-multi"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ollama": settings.OLLAMA_MODEL,
        "whisper": settings.WHISPER_MODEL,
        "tts": "elevenlabs",
        "restaurants": len(list(db.get_connection().execute("SELECT * FROM restaurants WHERE is_active=1").fetchall()))
    }

@app.websocket("/ws/voice/{call_sid}")
async def voice_handler(websocket: WebSocket, call_sid: str):
    """
    WebSocket handler pour Twilio - Multi-restaurant
    Flow: Identify restaurant → Load context → Handle call
    """
    await websocket.accept()
    print(f"\n🟢 [{call_sid}] Call connected")
    
    # TODO: Récupérer le numéro appelé depuis Twilio query params
    # Pour l'instant, on utilise le premier restaurant en DB
    restaurant = db.get_restaurant_by_phone("+33123456789")
    
    if not restaurant:
        print(f"❌ [{call_sid}] No restaurant found")
        await websocket.close()
        return
    
    print(f"🏪 [{call_sid}] Restaurant: {restaurant.name}")
    
    # Charger TOUT le contexte du restaurant
    menu = db.get_menu(restaurant.id)
    zones = db.get_delivery_zones(restaurant.id)
    hours = db.get_opening_hours(restaurant.id)
    
    print(f"📋 [{call_sid}] Loaded: {len(menu)} items, {len(zones)} zones, {len(hours)} hours")
    
    # Construire le prompt dynamique
    system_prompt = build_dynamic_prompt(restaurant, menu, zones, hours)
    
    # Initialize conversation state
    conversation_state = {
        "call_sid": call_sid,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "history": [],
        "start_time": datetime.now()
    }
    
    active_calls[call_sid] = conversation_state
    
    # Message de bienvenue personnalisé
    welcome = f"{restaurant.name} bonsoir ! Vous souhaitez commander à emporter ou en livraison ?"
    print(f"🤖 [{call_sid}] AI: {welcome}")
    
    try:
        # Envoyer message de bienvenue
        welcome_audio = await tts_service.synthesize(welcome)
        if welcome_audio:
            await websocket.send_text(json.dumps({
                "event": "media",
                "media": {
                    "payload": base64.b64encode(welcome_audio).decode()
                }
            }))
        
        # Main loop
        while True:
            # 1. Recevoir message de Twilio
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print(f"⏰ [{call_sid}] Timeout waiting for audio")
                continue
            
            data = json.loads(message)
            
            # 2. Traiter les événements Twilio
            if data.get("event") == "media":
                audio_payload = data["media"]["payload"]
                
                # Decode base64 audio
                audio_bytes = base64.b64decode(audio_payload)
                
                # 3. STT - Whisper
                print(f"🎤 [{call_sid}] Transcribing...")
                user_text = await stt_service.transcribe(audio_bytes)
                
                if not user_text or len(user_text) < 3:
                    continue
                
                print(f"👤 [{call_sid}] User: {user_text}")
                
                # 4. LLM - Ollama avec contexte restaurant
                print(f"🧠 [{call_sid}] Processing with LLM ({restaurant.name})...")
                ai_response = await llm_service.query(
                    prompt=user_text,
                    system_prompt=system_prompt,
                    history=conversation_state["history"]
                )
                
                print(f"🤖 [{call_sid}] AI: {ai_response}")
                
                # Save to history
                conversation_state["history"].append({
                    "user": user_text,
                    "assistant": ai_response
                })
                
                # 5. TTS - ElevenLabs
                print(f"🔊 [{call_sid}] Synthesizing speech...")
                audio_response = await tts_service.synthesize(ai_response)
                
                if not audio_response:
                    print(f"❌ [{call_sid}] TTS failed")
                    continue
                
                # 6. Envoyer audio à Twilio
                await websocket.send_text(json.dumps({
                    "event": "media",
                    "media": {
                        "payload": base64.b64encode(audio_response).decode()
                    }
                }))
                
                print(f"✅ [{call_sid}] Response sent\n")
            
            elif data.get("event") == "stop":
                print(f"🔴 [{call_sid}] Call ended by Twilio")
                break
    
    except WebSocketDisconnect:
        print(f"🔴 [{call_sid}] WebSocket disconnected")
    
    except Exception as e:
        print(f"❌ [{call_sid}] Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup & stats
        if call_sid in active_calls:
            duration = (datetime.now() - conversation_state["start_time"]).seconds
            print(f"📊 [{call_sid}] Call duration: {duration}s")
            print(f"📊 [{call_sid}] Exchanges: {len(conversation_state['history'])}")
            print(f"🏪 [{call_sid}] Restaurant: {restaurant.name}")
            
            # TODO: Save order to database
            
            del active_calls[call_sid]

@app.get("/calls")
async def list_calls():
    """Debug: voir les appels actifs"""
    return {
        "active_calls": len(active_calls),
        "calls": [
            {
                "call_sid": cid,
                "restaurant": state["restaurant_name"],
                "duration_seconds": (datetime.now() - state["start_time"]).seconds
            }
            for cid, state in active_calls.items()
        ]
    }

@app.get("/restaurants")
async def list_restaurants():
    """Debug: voir les restaurants"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, city, twilio_phone, is_active FROM restaurants")
    
    restaurants = []
    for row in cursor.fetchall():
        restaurants.append({
            "id": row[0],
            "name": row[1],
            "city": row[2],
            "phone": row[3],
            "active": bool(row[4])
        })
    
    conn.close()
    return {"count": len(restaurants), "restaurants": restaurants}

if __name__ == "__main__":
    print("🚀 Starting Pizza Agent AI - Multi Restaurant...")
    print(f"📍 Server: {settings.HOST}:{settings.PORT}")
    print(f"🤖 LLM: {settings.OLLAMA_MODEL}")
    print(f"🎤 STT: Whisper {settings.WHISPER_MODEL}")
    print(f"🔊 TTS: ElevenLabs")
    print(f"🗄️  Database: SQLite")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )
