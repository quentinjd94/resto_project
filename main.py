from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
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
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM restaurants WHERE is_active=1")
        count = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        print(f"Error in health check: {e}")
        count = 0
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ollama": settings.OLLAMA_MODEL,
        "whisper": settings.WHISPER_MODEL,
        "tts": "elevenlabs",
        "restaurants": count
    }

@app.get("/restaurants")
async def list_restaurants():
    """Debug: voir les restaurants"""
    try:
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
    except Exception as e:
        return {"error": str(e)}

@app.post("/ws/voice")
async def voice_webhook(request: Request):
    """
    Endpoint HTTP pour Twilio - Retourne TwiML pour démarrer le WebSocket
    """
    # Récupérer les paramètres Twilio
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    
    print(f"\n📞 Incoming call: {call_sid}")
    
    # TwiML pour connecter au WebSocket
    # IMPORTANT: Remplace par ton URL ngrok
    websocket_url = "wss://studentless-simone-nonpreventive.ngrok-free.dev/ws/voice/" + call_sid
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{websocket_url}" />
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/ws/voice")
async def voice_webhook(request: Request):
    """
    Endpoint HTTP pour Twilio - Retourne TwiML pour démarrer le WebSocket
    """
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    
    print(f"\n📞 Incoming call: {call_sid}")
    
    # IMPORTANT: Utilise ton URL ngrok actuelle
    websocket_url = "wss://studentless-simone-nonpreventive.ngrok-free.dev/ws/voice/" + call_sid
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{websocket_url}" />
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

@app.websocket("/ws/voice/{call_sid}")
async def voice_handler(websocket: WebSocket, call_sid: str):
    """
    WebSocket handler pour Twilio - Multi-restaurant
    """
    await websocket.accept()
    print(f"\n🟢 [{call_sid}] Call connected")
    
    try:
        # Récupérer le premier restaurant (pour test)
        restaurant = db.get_restaurant_by_phone("+33123456789")
        
        if not restaurant:
            print(f"❌ [{call_sid}] No restaurant found")
            await websocket.close()
            return
        
        print(f"🏪 [{call_sid}] Restaurant: {restaurant.name}")
        
        # Charger contexte
        menu = db.get_menu(restaurant.id)
        zones = db.get_delivery_zones(restaurant.id)
        hours = db.get_opening_hours(restaurant.id)
        
        print(f"📋 [{call_sid}] Loaded: {len(menu)} items, {len(zones)} zones")
        
        # Construire prompt
        system_prompt = build_dynamic_prompt(restaurant, menu, zones, hours)
        
        # State
        conversation_state = {
            "call_sid": call_sid,
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "history": [],
            "start_time": datetime.now()
        }
        
        active_calls[call_sid] = conversation_state
        
        # Welcome message
        welcome = f"{restaurant.name} bonsoir ! Vous souhaitez commander à emporter ou en livraison ?"
        print(f"🤖 [{call_sid}] AI: {welcome}")
        
        # Send welcome audio
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
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print(f"⏰ [{call_sid}] Timeout")
                continue
            
            data = json.loads(message)
            
            if data.get("event") == "media":
                audio_payload = data["media"]["payload"]
                audio_bytes = base64.b64decode(audio_payload)
                
                # STT
                print(f"🎤 [{call_sid}] Transcribing...")
                user_text = await stt_service.transcribe(audio_bytes)
                
                if not user_text or len(user_text) < 3:
                    continue
                
                print(f"👤 [{call_sid}] User: {user_text}")
                
                # LLM
                print(f"🧠 [{call_sid}] Processing...")
                ai_response = await llm_service.query(
                    prompt=user_text,
                    system_prompt=system_prompt,
                    history=conversation_state["history"]
                )
                
                print(f"🤖 [{call_sid}] AI: {ai_response}")
                
                conversation_state["history"].append({
                    "user": user_text,
                    "assistant": ai_response
                })
                
                # TTS
                print(f"🔊 [{call_sid}] Synthesizing...")
                audio_response = await tts_service.synthesize(ai_response)
                
                if audio_response:
                    await websocket.send_text(json.dumps({
                        "event": "media",
                        "media": {
                            "payload": base64.b64encode(audio_response).decode()
                        }
                    }))
                    print(f"✅ [{call_sid}] Response sent\n")
            
            elif data.get("event") == "stop":
                print(f"🔴 [{call_sid}] Call ended")
                break
    
    except WebSocketDisconnect:
        print(f"🔴 [{call_sid}] Disconnected")
    except Exception as e:
        print(f"❌ [{call_sid}] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if call_sid in active_calls:
            duration = (datetime.now() - conversation_state["start_time"]).seconds
            print(f"📊 [{call_sid}] Duration: {duration}s, Exchanges: {len(conversation_state['history'])}")
            del active_calls[call_sid]

@app.get("/calls")
async def list_calls():
    """Debug: appels actifs"""
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
