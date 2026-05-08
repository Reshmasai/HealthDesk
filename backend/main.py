# main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, get_db, Base
from models import Message
from ai_service import get_health_guidance

# Create tables automatically on startup
Base.metadata.create_all(bind=engine)

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
    return {"message": "HealthDesk API running"}


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    """Fetch all messages from SQLite ordered oldest first."""
    messages = db.query(Message).order_by(Message.timestamp).all()
    return {
        "items": [
            {
                "id":        m.id,
                "name":      m.name,
                "role":      m.role,
                "text":      m.text,
                "severity":  m.severity,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]
    }


@app.post("/query")
def handle_query(query: HealthQuery, db: Session = Depends(get_db)):
    """
    1. Fetch existing chat history from SQLite
    2. Save user message
    3. Pass history + new message to AI
    4. Save AI response
    5. Return to Angular
    """

    # 1. Fetch existing conversation history for this user from SQLite
    previous_messages = (
        db.query(Message)
        .filter(Message.name == query.name)   # only this user's messages
        .order_by(Message.timestamp)
        .all()
    )

    # Convert to simple dicts for ai_service
    history = [
        {"role": m.role, "text": m.text}
        for m in previous_messages
    ]

    # 2. Save user message to SQLite
    user_msg = Message(
        name=query.name,
        role="user",
        text=query.symptoms,
        severity=query.severity,
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    db.commit()

    # 3. Call AI with full history for multi-turn memory
    ai_response = get_health_guidance(
        name=query.name,
        symptoms=query.symptoms,
        severity=query.severity,
        history=history          # ← passing conversation history
    )

    # 4. Save AI response to SQLite
    ai_msg = Message(
        name=query.name,
        role="ai",
        text=ai_response,
        timestamp=datetime.utcnow()
    )
    db.add(ai_msg)
    db.commit()

    return {"ai_response": ai_response}


@app.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    """Clear all chat history — useful for testing."""
    db.query(Message).delete()
    db.commit()
    return {"message": "History cleared"}