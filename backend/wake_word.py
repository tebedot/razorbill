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

load_dotenv()

# We use the pre-trained "alexa" model as a stand-in for "Razor Bill" 
# until a custom model is trained for "Razor Bill".
WAKE_WORD = "alexa"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280
SILENCE_THRESHOLD = 500  # Adjust based on mic sensitivity
SILENCE_CHUNKS = 20      # Number of consecutive silent chunks to stop recording

def is_silent(data_chunk):
    """Returns True if the chunk is below the silence threshold."""
    # Convert to float32 to avoid overflow when squaring int16 values
    audio_data = np.frombuffer(data_chunk, dtype=np.int16).astype(np.float32)
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms < SILENCE_THRESHOLD

def record_command(pa, stream):
    """Records audio from the mic until silence is detected."""
    print("Merekam perintah... (Silakan bicara)")
    frames = []
    silent_chunks_count = 0
    has_spoken = False
    
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        if is_silent(data):
            if has_spoken:
                silent_chunks_count += 1
        else:
            has_spoken = True
            silent_chunks_count = 0
            
        if has_spoken and silent_chunks_count > SILENCE_CHUNKS:
            break
            
        # Timeout after a while to prevent infinite recording
        if len(frames) > 500: # approx 40 seconds
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

def listen_loop():
    # Ensure models are downloaded before trying to load them
    print("Memeriksa dan mengunduh model openWakeWord (jika belum ada)...")
    import openwakeword.utils
    openwakeword.utils.download_models()
    
    # Load openWakeWord model
    print("Memuat model openWakeWord...")
    oww_model = Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")
    
    pa = pyaudio.PyAudio()
    mic_stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print(f"Razor Bill (backend audio) telah aktif. Ucapkan '{WAKE_WORD}' untuk memanggil.")
    
    try:
        while True:
            audio = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
            
            # Feed audio to wake word model
            prediction = oww_model.predict(audio)
            
            # Check if wake word is detected
            if prediction[WAKE_WORD] > 0.5:
                print(f"\n[{WAKE_WORD.upper()} DETECTED]")
                
                # Record user's command
                cmd_wav = record_command(pa, mic_stream)
                
                # Transcribe
                print("Menerjemahkan audio ke teks (STT)...")
                user_text = transcribe_audio(cmd_wav)
                print(f"User: {user_text}")
                
                if not user_text.strip():
                    print("Suara tidak terdengar jelas.")
                    continue
                
                # Send to AI
                messages = [
                    {"role": "system", "content": "Your name is Razor Bill (or Razor/Bill). You are a highly polite British butler similar to Alfred Pennyworth. Respond concisely."},
                    {"role": "user", "content": user_text}
                ]
                print("Berpikir...")
                response = generate_chat_response(messages, stream=False)
                
                # Extract the final answer (skipping reasoning tokens since stream=False returns full response)
                ai_text = response.choices[0].message.content
                print(f"Razor Bill: {ai_text}")
                
                # Synthesize Speech (TTS)
                print("Menghasilkan suara (TTS)...")
                try:
                    audio_bytes = synthesize_speech(ai_text)
                    play_audio(audio_bytes)
                except Exception as e:
                    print(f"Gagal memutar suara TTS: {e}")
                
                print(f"\nMelanjutkan mode siaga. Ucapkan '{WAKE_WORD}' untuk memanggil lagi.")
                
    except KeyboardInterrupt:
        print("\nMematikan layanan audio Razor Bill.")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        pa.terminate()

if __name__ == "__main__":
    listen_loop()
