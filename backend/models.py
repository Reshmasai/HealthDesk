# models.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class Message(Base):
    __tablename__ = "messages"

    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String, nullable=False)
    role      = Column(String, nullable=False)   # "user" or "ai"
    text      = Column(String, nullable=False)
    severity  = Column(String, nullable=True)    # only set for user messages
    timestamp = Column(DateTime, default=datetime.utcnow)