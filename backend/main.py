from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Razor Bill API", version="0.1.0")

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/", response_model=HealthResponse)
def read_root():
    return {"status": "ok", "message": "Razor Bill API is running"}
