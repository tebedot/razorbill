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
    messages = [
        {"role": "system", "content": "You are Razor Bill, a helpful AI assistant. You think carefully before answering."},
        {"role": "user", "content": request.message}
    ]
    
    # Returning a StreamingResponse so the UI can stream the tokens (including thinking process)
    return StreamingResponse(
        ai_engine.stream_chat_response(messages),
        media_type="text/plain"
    )
