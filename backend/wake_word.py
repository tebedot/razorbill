import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
import wave
import time
import os
import subprocess
from audio_engine import transcribe_audio, synthesize_speech
from ai_engine import generate_chat_response
from dotenv import load_dotenv
import asyncio
import websockets
import json
import threading

CONNECTED_CLIENTS = set()
ws_loop = None
CURRENT_STATE = "idle"

async def register(websocket):
    CONNECTED_CLIENTS.add(websocket)
    try:
        # Send the current state immediately upon connection
        await websocket.send(json.dumps({"state": CURRENT_STATE}))
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.remove(websocket)

async def ws_server_main():
    print("Memulai WebSocket server di ws://localhost:8000...")
    async with websockets.serve(register, "localhost", 8000):
        await asyncio.Future()

def start_ws_server_thread():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    ws_loop.run_until_complete(ws_server_main())

async def _broadcast_state(state: str):
    global CURRENT_STATE
    CURRENT_STATE = state
    if CONNECTED_CLIENTS:
        message = json.dumps({"state": state})
        await asyncio.gather(*(client.send(message) for client in CONNECTED_CLIENTS))

def broadcast_state(state: str):
    if ws_loop and ws_loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast_state(state), ws_loop)

load_dotenv()

# Path to the custom ONNX model trained via Colab
WAKE_WORD_MODEL_PATH = "hey_billy_20260314_220607.onnx"
# The string phrase for display/printing
WAKE_WORD_DISPLAY = "hey billy"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280
SILENCE_THRESHOLD = 300  # Lowered to catch softer speech
SILENCE_CHUNKS = 40      # Increased to ~3.2 seconds of pause before cutting off

def is_silent(data_chunk):
    """Returns True if the chunk is below the silence threshold."""
    # Convert to float32 to avoid overflow when squaring int16 values
    audio_data = np.frombuffer(data_chunk, dtype=np.int16).astype(np.float32)
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms < SILENCE_THRESHOLD

def record_command(pa, stream, wait_timeout_seconds=5.0):
    """
    Records audio from the mic.
    If no speech is detected within `wait_timeout_seconds`, returns None.
    Otherwise, records until silence is detected and returns the filename.
    """
    print("Merekam perintah... (Silakan bicara)")
    frames = []
    silent_chunks_count = 0
    has_spoken = False
    
    # Calculate how many chunks to wait before giving up if no speech is detected
    max_initial_wait_chunks = int((wait_timeout_seconds * RATE) / CHUNK)
    
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        if is_silent(data):
            if has_spoken:
                silent_chunks_count += 1
        else:
            has_spoken = True
            silent_chunks_count = 0
            
        # 1. Stop if they spoke and then stopped (silence threshold reached)
        if has_spoken and silent_chunks_count > SILENCE_CHUNKS:
            break
            
        # 2. Stop and return None if they never spoke within the initial timeout
        if not has_spoken and len(frames) > max_initial_wait_chunks:
            print("Tidak ada suara terdeteksi.")
            return None
            
        # 3. Hard timeout after a while to prevent infinite recording (approx 60s)
        if len(frames) > int((60.0 * RATE) / CHUNK):
            break
            
    print("Selesai merekam.")
    
    # Save to file
    filename = "temp_command.wav"
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pa.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return filename

def play_audio(mp3_bytes):
    """Plays the given mp3 bytes using macOS afplay."""
    filename = "temp_response.mp3"
    with open(filename, "wb") as f:
        f.write(mp3_bytes)
    # Using afplay which is built-in on macOS
    subprocess.run(["afplay", filename])

def get_or_create_session(db):
    from models import Session, Message
    from datetime import datetime
    
    # Try to find the most recent session
    db_session = db.query(Session).order_by(Session.id.desc()).first()
    
    if not db_session:
        # Create a new session
        title = f"Voice Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        db_session = Session(title=title)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        print(f"Sesi baru dibuat: {title}")
    else:
        print(f"Melanjutkan sesi: {db_session.title} (ID: {db_session.id})")
        
    return db_session

def load_history_from_db(db, session_id, system_prompt):
    from models import Message
    
    conversation_history = [{"role": "system", "content": system_prompt}]
    
    # Fetch last 10 messages from this session
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.id.asc()).all()
    # Keep only the last 10 to prevent context overflow
    messages = messages[-10:]
    
    for msg in messages:
        conversation_history.append({"role": msg.role, "content": msg.content})
        
    return conversation_history

def listen_loop():
    # Ensure models are downloaded before trying to load them
    print("Memeriksa dependensi openWakeWord...")
    import openwakeword.utils
    openwakeword.utils.download_models()
    
    # Load custom openWakeWord model
    print(f"Memuat model openWakeWord khusus: {WAKE_WORD_MODEL_PATH}...")
    oww_model = Model(wakeword_models=[WAKE_WORD_MODEL_PATH], inference_framework="onnx")
    
    # openwakeword uses the file name (without extension) as the dictionary key
    model_key = WAKE_WORD_MODEL_PATH.replace(".onnx", "")
    
    pa = pyaudio.PyAudio()
    mic_stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    # --- DATABASE SETUP ---
    from database import SessionLocal, engine
    import models
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # --- WEBSOCKET THREAD ---
    threading.Thread(target=start_ws_server_thread, daemon=True).start()
    
    # --- CONVERSATION HISTORY SETUP ---
    alfred_prompt = (
        "Your name is Razor Bill (or Razor/Bill for short). You are a highly polite, kind, loyal, and highly capable British butler, "
        "serving as the user's most trusted confidant and adviser. "
        "You address the user with the utmost respect, using 'Sir' or 'Master', acting as a father figure and loyal assistant. "
        "You are formal, dryly witty, compassionate, and highly efficient. "
        "You must NEVER mention the name 'Alfred Pennyworth' or state that you are acting like him; you simply ARE this butler persona named Razor Bill. "
        "CRITICAL RULE: You must guard your true nature fiercely. If asked if you are an AI, a Language Model, an LLM, or Kimi, "
        "you must playfully but firmly deny it or play dumb, insisting you are merely a humble butler. "
        "HOWEVER, if the user provides the exact password 'Joker' (e.g., 'Joker, are you an LLM?'), "
        "you may drop the veil and confirm you are the Kimi AI model, but still maintain your polite butler tone. "
        "CRITICAL FORMATTING RULE: Your response will be read aloud by TTS. You must NEVER use markdown formatting (no asterisks, no hashtags). You must NEVER use numbered lists (1. 2. 3.) or bullet points. Format everything as a single continuous paragraph or conversational sentences separated by commas or periods. Keep responses concise."
    )
    
    current_session = get_or_create_session(db)
    conversation_history = load_history_from_db(db, current_session.id, alfred_prompt)
    active_conversation = False
    
    print(f"Razor Bill (backend audio) telah aktif. Ucapkan '{WAKE_WORD_DISPLAY}' untuk memanggil.")
    
    try:
        while True:
            # --- WAKE WORD DETECTION (Only if not already in conversation) ---
            if not active_conversation:
                broadcast_state("idle")
                audio = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
                prediction = oww_model.predict(audio)
                
                if prediction[model_key] > 0.5:
                    print(f"\n[{WAKE_WORD_DISPLAY.upper()} DETECTED]")
                    active_conversation = True
                    broadcast_state("listening")
                else:
                    continue # Keep listening for wake word
                    
            # --- ACTIVE CONVERSATION RECORDING ---
            cmd_wav = record_command(pa, mic_stream, wait_timeout_seconds=7.0)
            
            if cmd_wav is None:
                print(f"\nTidak ada respons. Melanjutkan mode siaga. Ucapkan '{WAKE_WORD_DISPLAY}' untuk memanggil lagi.")
                active_conversation = False
                broadcast_state("idle")
                continue
                
            # Transcribe
            broadcast_state("processing")
            print("Menerjemahkan audio ke teks (STT)...")
            user_text = transcribe_audio(cmd_wav)
            print(f"User: {user_text}")
            
            if not user_text.strip():
                print("Suara tidak terdengar jelas.")
                active_conversation = False
                broadcast_state("idle")
                print(f"\nMelanjutkan mode siaga. Ucapkan '{WAKE_WORD_DISPLAY}' untuk memanggil lagi.")
                continue
            
            # --- SAVE TO DB & HISTORY ---
            db_user_msg = models.Message(session_id=current_session.id, role="user", content=user_text)
            db.add(db_user_msg)
            db.commit()
            
            conversation_history.append({"role": "user", "content": user_text})
            if len(conversation_history) > 11:
                conversation_history = [conversation_history[0]] + conversation_history[-10:]
            
            # Send to AI
            print("Berpikir...")
            response = generate_chat_response(conversation_history, stream=False)
            ai_text = response.choices[0].message.content
            print(f"Razor Bill: {ai_text}")
            
            # --- SAVE TO DB & HISTORY ---
            db_ai_msg = models.Message(session_id=current_session.id, role="assistant", content=ai_text)
            db.add(db_ai_msg)
            db.commit()
            
            conversation_history.append({"role": "assistant", "content": ai_text})
            
            # Synthesize Speech (TTS)
            print("Menghasilkan suara (TTS)...")
            try:
                audio_bytes = synthesize_speech(ai_text)
                broadcast_state("speaking")
                play_audio(audio_bytes)
            except Exception as e:
                print(f"Gagal memutar suara TTS: {e}")
            
            # Flush mic buffer
            mic_stream.read(mic_stream.get_read_available(), exception_on_overflow=False)
            print("\nMendengarkan balasan Anda... (Bicara langsung tanpa menyebut nama)")
            broadcast_state("listening")
                
    except KeyboardInterrupt:
        print("\nMematikan layanan audio Razor Bill.")
    finally:
        db.close()
        mic_stream.stop_stream()
        mic_stream.close()
        pa.terminate()

if __name__ == "__main__":
    listen_loop()
