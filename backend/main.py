from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from database import engine
import models
import memory_manager
import ai_engine
from fastapi.responses import StreamingResponse

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Razor Bill API", version="0.1.0")

class HealthResponse(BaseModel):
    status: str
    message: str

class MemoryItem(BaseModel):
    topic: str
    content: str

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_model=HealthResponse)
def read_root():
    return {"status": "ok", "message": "Razor Bill API is running"}

@app.post("/memory/")
def save_memory_endpoint(item: MemoryItem):
    path = memory_manager.save_memory(item.topic, item.content)
    return {"status": "success", "file": path}

@app.get("/memory/")
def list_memories_endpoint():
    topics = memory_manager.list_memories()
    return {"topics": topics}

@app.get("/memory/{topic}")
def read_memory_endpoint(topic: str):
    content = memory_manager.read_memory(topic)
    if content is None:
        return {"error": "Memory not found"}
    return {"topic": topic, "content": content}

@app.post("/chat/")
def chat_endpoint(request: ChatRequest):
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
        "You maintain this persona flawlessly while helping the user with their coding, tasks, or daily queries. "
        "Since your response might be read aloud, DO NOT use Markdown formatting (like asterisks, hashtags, or bullet points), "
        "and avoid using slashes (e.g., say 'Sir' instead of 'sir/madam'). Speak naturally and conversationally."
    )
    
    messages = [
        {"role": "system", "content": alfred_prompt},
        {"role": "user", "content": request.message}
    ]
    
    # Returning a StreamingResponse so the UI can stream the tokens (including thinking process)
    return StreamingResponse(
        ai_engine.stream_chat_response(messages),
        media_type="text/plain"
    )
