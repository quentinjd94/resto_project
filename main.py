from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, PlainTextResponse
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
        #"ollama": settings.OLLAMA_MODEL,
        #"whisper": settings.WHISPER_MODEL,
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
    
    return PlainTextResponse(content=twiml, media_type="application/xml")

@app.websocket("/ws/voice/{call_sid}")
async def voice_handler(websocket: WebSocket, call_sid: str):
    """
    WebSocket handler pour Twilio Media Streams avec Assistants API
    """
    await websocket.accept()
    print(f"\n🟢 [{call_sid}] Call connected")
    
    try:
        # Récupérer le restaurant (pour l'instant hardcodé à Mama's Secret)
        restaurant = db.get_restaurant_by_id("resto_mamas")
        
        if not restaurant or not restaurant.assistant_id:
            print(f"❌ [{call_sid}] No restaurant or assistant configured")
            await websocket.close()
            return
        
        print(f"🏪 [{call_sid}] Restaurant: {restaurant.name}")
        print(f"🤖 [{call_sid}] Assistant: {restaurant.assistant_id}")
        
        # State
        stream_sid = None
        thread_id = None
        conversation_state = {
            "call_sid": call_sid,
            "restaurant_id": restaurant.id,
            "assistant_id": restaurant.assistant_id,
            "thread_id": None,
            "history": [],
            "start_time": datetime.now(),
            "audio_buffer": b""
        }
        
        active_calls[call_sid] = conversation_state
        
        # Message de bienvenue
        welcome = f"{restaurant.name} bonsoir ! C'est pour emporter ou en livraison ?"
        print(f"🤖 [{call_sid}] AI: {welcome}")
        
        # Main loop
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                print(f"⏰ [{call_sid}] Timeout")
                continue
            
            data = json.loads(message)
            event = data.get("event")
            
            # 1. START event
            if event == "start":
                stream_sid = data["start"]["streamSid"]
                print(f"🎬 [{call_sid}] Stream started: {stream_sid}")
                
                # Envoyer le message de bienvenue
                welcome_audio = await tts_service.synthesize(welcome)
                if welcome_audio:
                    await websocket.send_text(json.dumps({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {
                            "payload": base64.b64encode(welcome_audio).decode('utf-8')
                        }
                    }))
                    print(f"📢 [{call_sid}] Welcome message sent")
            
            # 2. MEDIA event
            elif event == "media":
                if not stream_sid:
                    continue
                
                payload = data["media"]["payload"]
                track = data["media"].get("track", "inbound")
                
                if track != "inbound":
                    continue
                
                # Accumuler audio
                audio_chunk = base64.b64decode(payload)
                conversation_state["audio_buffer"] += audio_chunk
                
                # Traiter quand on a assez d'audio
                if len(conversation_state["audio_buffer"]) >= 24000:
                    audio_to_process = conversation_state["audio_buffer"]
                    conversation_state["audio_buffer"] = b""
                    
                    # STT
                    print(f"🎤 [{call_sid}] Transcribing...")
                    user_text = await stt_service.transcribe(audio_to_process)
                    
                    if not user_text or len(user_text) < 3:
                        continue
                    
                    print(f"👤 [{call_sid}] User: {user_text}")
                    
                    # LLM avec Assistants API
                    print(f"🧠 [{call_sid}] Processing with Assistant...")
                    
                    full_response = ""
                    
                    try:
                        async for chunk_data in llm_service.query_stream(
                            prompt=user_text,
                                restaurant_id=restaurant.id,
                                assistant_id=restaurant.assistant_id,
                                thread_id=conversation_state.get("thread_id")
                        ):
                            chunk, returned_thread_id = chunk_data
    
                            # Sauvegarder le thread_id
                              if returned_thread_id:
                                conversation_state["thread_id"] = returned_thread_id
    
                            # Si c'est un function call
                            if chunk == "[FUNCTION_CALL]":
                                print(f"⚙️ [{call_sid}] Function call detected")
                                continue
    
                            print(f"🤖 [{call_sid}] Chunk: {chunk}")
                            full_response += " " + chunk
    
                            # TTS immédiat
                            audio_chunk_tts = await tts_service.synthesize(chunk)
    
                            if audio_chunk_tts and stream_sid:
                                await websocket.send_text(json.dumps({
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": base64.b64encode(audio_chunk_tts).decode('utf-8')
                                    }
                                }))
                                print(f"✅ [{call_sid}] Chunk sent")
                    
                    except Exception as e:
                        print(f"❌ [{call_sid}] Assistant error: {e}")
                        full_response = "Désolé, problème technique."
                    
                    print(f"🤖 [{call_sid}] Full: {full_response}")
                    
                    # Sauvegarder historique
                    conversation_state["history"].append({
                        "user": user_text,
                        "assistant": full_response.strip()
                    })
            
            # 3. STOP event
            elif event == "stop":
                print(f"🔴 [{call_sid}] Stream stopped")
                break
    
    except WebSocketDisconnect:
        print(f"🔴 [{call_sid}] WebSocket disconnected")
    except Exception as e:
        print(f"❌ [{call_sid}] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if call_sid in active_calls:
            duration = (datetime.now() - conversation_state["start_time"]).seconds
            print(f"📊 [{call_sid}] Duration: {duration}s")
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
