from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_service import get_health_guidance
from store import add_message, get_history
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthQuery(BaseModel):
    name: str
    symptoms: str
    severity: str

@app.get("/")
def root():
    return {"message": "HealthDesk API running"}  # fixed: key was inside the string before

@app.get("/history")
def history():
    return {"items": get_history()}

@app.post("/query")
def handle_query(query: HealthQuery):

    add_message({
        "name": query.name,
        "role": "user",
        "text": query.symptoms,
        "severity": query.severity,
        "timestamp": datetime.utcnow().isoformat()
    })

    ai_response = get_health_guidance(
        query.name,
        query.symptoms,
        query.severity
    )

    add_message({
        "name": query.name,
        "role": "ai",
        "text": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"ai_response": ai_response}  # returns a plain string — no [object Object]