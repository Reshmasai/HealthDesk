# main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, get_db, Base
from models import Message
from ai_service import get_health_guidance

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HealthDesk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom validation error handler 
# By default FastAPI returns a complex 422 error — this makes it cleaner
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    messages = [f"{e['loc'][-1]}: {e['msg']}" for e in errors]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": messages}
    )


# Request model with Pydantic validators
VALID_SEVERITIES = {"low", "medium", "high"}

class HealthQuery(BaseModel):
    name: str
    symptoms: str
    severity: str

    @validator("name")
    def name_must_not_be_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @validator("symptoms")
    def symptoms_must_not_be_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Symptoms cannot be empty")
        if len(v) < 3:
            raise ValueError("Please describe your symptoms in more detail")
        if len(v) > 500:
            raise ValueError("Symptoms description is too long (max 500 characters)")
        return v

    @validator("severity")
    def severity_must_be_valid(cls, v):
        if v.lower() not in VALID_SEVERITIES:
            raise ValueError(f"Severity must be one of: Low, Medium, High")
        return v.capitalize()  # normalize to "Low", "Medium", "High"


# Routes

@app.get("/")
def root():
    return {"message": "HealthDesk API running", "version": "1.0.0"}


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    """Fetch all messages from SQLite ordered oldest first."""
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )


@app.get("/history/{name}")
def get_history_by_user(name: str, db: Session = Depends(get_db)):
    """
    Fetch chat history for a specific user by name.
    Returns 404 if user has no history at all.
    """
    name = name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name parameter cannot be empty"
        )

    try:
        messages = (
            db.query(Message)
            .filter(Message.name == name)
            .order_by(Message.timestamp)
            .all()
        )

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No chat history found for user '{name}'"
            )

        return {
            "user": name,
            "total": len(messages),
            "items": [
                {
                    "id":        m.id,
                    "role":      m.role,
                    "text":      m.text,
                    "severity":  m.severity,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in messages
            ]
        }
    except HTTPException:
        raise  # re-raise our own HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history for user '{name}': {str(e)}"
        )


@app.post("/query", status_code=status.HTTP_200_OK)
def handle_query(query: HealthQuery, db: Session = Depends(get_db)):
    """
    Validate input, fetch history, call AI, persist messages.
    Pydantic validators run automatically before this function is called.
    """
    try:
        # Fetch conversation history for this user
        previous_messages = (
            db.query(Message)
            .filter(Message.name == query.name)
            .order_by(Message.timestamp)
            .all()
        )
        history = [{"role": m.role, "text": m.text} for m in previous_messages]

        # Save user message
        user_msg = Message(
            name=query.name,
            role="user",
            text=query.symptoms,
            severity=query.severity,
            timestamp=datetime.utcnow()
        )
        db.add(user_msg)
        db.commit()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    # Call AI — separate try/except so DB errors and AI errors are distinct
    try:
        ai_response = get_health_guidance(
            name=query.name,
            symptoms=query.symptoms,
            severity=query.severity,
            history=history
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

    # Save AI response
    try:
        ai_msg = Message(
            name=query.name,
            role="ai",
            text=ai_response,
            timestamp=datetime.utcnow()
        )
        db.add(ai_msg)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save AI response: {str(e)}"
        )

    return {"ai_response": ai_response}


@app.delete("/history")
def clear_all_history(db: Session = Depends(get_db)):
    """Clear ALL chat history — for testing only."""
    try:
        deleted = db.query(Message).delete()
        db.commit()
        return {"message": f"Cleared {deleted} messages"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )


@app.delete("/history/{name}")
def clear_user_history(name: str, db: Session = Depends(get_db)):
    """Clear chat history for a specific user."""
    try:
        deleted = db.query(Message).filter(Message.name == name).delete()
        db.commit()
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No history found for user '{name}'"
            )
        return {"message": f"Cleared {deleted} messages for '{name}'"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )