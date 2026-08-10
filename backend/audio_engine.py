import os
import httpx
from faster_whisper import WhisperModel

# Initialize Whisper model (we'll use 'base' for faster local processing, can be upgraded to 'small' or 'medium' later)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        # Load the model on first use to save initial startup time
        # Using 'cpu' by default since this is a Mac. If it's an M-series Mac, 
        # faster-whisper doesn't fully utilize CoreML yet, but 'cpu' works fine.
        whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return whisper_model

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes the given audio file using faster-whisper.
    """
    model = get_whisper_model()
    segments, info = model.transcribe(file_path, beam_size=5)
    
    text = "".join([segment.text for segment in segments])
    return text.strip()

def synthesize_speech(text: str) -> bytes:
    """
    Synthesizes speech from text using Fish Audio API.
    Returns the audio bytes (e.g., mp3).
    """
    api_key = os.environ.get("FISH_AUDIO_API_KEY")
    if not api_key:
        raise ValueError("FISH_AUDIO_API_KEY environment variable is not set")
        
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        # The specific model ID provided by the user for the Alfred persona
        "reference_id": "ece8efe2159a4d5b9fadd53df04ffb22",
        "format": "mp3",
        "latency": "normal"
    }
    
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload, timeout=30.0)
        
        if response.status_code != 200:
            raise Exception(f"Fish Audio API error {response.status_code}: {response.text}")
            
        return response.content
