# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This creates a single healthdesk.db file inside your backend folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./healthdesk.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite only
)

# Each request gets its own DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# Dependency — inject this into any FastAPI route with Depends()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()