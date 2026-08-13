from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, SessionLocal
import models
import memory_manager
import ai_engine
from datetime import datetime

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Razor Bill API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_session(db):
    db_session = db.query(models.Session).order_by(models.Session.id.desc()).first()
    if not db_session:
        title = f"Dashboard Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        db_session = models.Session(title=title)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    return db_session

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

@app.get("/messages")
def get_messages():
    db = SessionLocal()
    try:
        session = get_current_session(db)
        messages = db.query(models.Message).filter(models.Message.session_id == session.id).order_by(models.Message.id.asc()).all()
        return {
            "session_id": session.id, 
            "messages": [{"id": msg.id, "role": msg.role, "content": msg.content} for msg in messages]
        }
    finally:
        db.close()

@app.post("/chat/")
def chat_endpoint(request: ChatRequest):
    db = SessionLocal()
    try:
        session = get_current_session(db)
        
        # Save user message
        user_msg = models.Message(session_id=session.id, role="user", content=request.message)
        db.add(user_msg)
        db.commit()
        
        alfred_prompt = (
            "Your name is Razor Bill (or Razor/Bill for short). You are a highly polite, kind, loyal, and highly capable British butler, "
            "serving as the user's most trusted confidant and adviser. "
            "You address the user with the utmost respect, using 'Sir' or 'Master', acting as a father figure and loyal assistant. "
            "You are formal, dryly witty, compassionate, and highly efficient. "
            "You must NEVER mention the name 'Alfred Pennyworth' or state that you are acting like him; you simply ARE this butler persona named Razor Bill. "
            "CRITICAL RULE: You must guard your true nature fiercely. If asked if you are an AI, a Language Model, an LLM, or Kimi, "
            "you must playfully but firmly deny it or play dumb, insisting you are merely a humble butler. "
            "CRITICAL FORMATTING RULE: You must NEVER use markdown formatting (no asterisks, no hashtags). You must NEVER use numbered lists (1. 2. 3.) or bullet points. Format everything as a single continuous paragraph or conversational sentences separated by commas or periods. Keep responses concise."
        )
        
        history = [{"role": "system", "content": alfred_prompt}]
        db_messages = db.query(models.Message).filter(models.Message.session_id == session.id).order_by(models.Message.id.asc()).all()[-10:]
        for m in db_messages:
            history.append({"role": m.role, "content": m.content})
            
        # Get AI response
        response = ai_engine.generate_chat_response(history, stream=False)
        ai_text = response.choices[0].message.content
        
        # Save AI response
        ai_msg = models.Message(session_id=session.id, role="assistant", content=ai_text)
        db.add(ai_msg)
        db.commit()
        
        return {"id": ai_msg.id, "role": ai_msg.role, "content": ai_text}
    finally:
        db.close()
