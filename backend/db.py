import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ai_dubbing")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String(12), primary_key=True)
    status = Column(String(50), default="queued")
    error = Column(String(500), nullable=True)
    download_url = Column(String(500), nullable=True)
    audio_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    transcript_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(32), nullable=False)
    rating = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    email = Column(String(320), nullable=True)
    page = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BetaToken(Base):
    __tablename__ = "beta_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    allowed_seconds = Column(Float, nullable=False, default=180.0)
    used_seconds = Column(Float, nullable=False, default=0.0)
    reserved_seconds = Column(Float, nullable=False, default=0.0)
    active_job_id = Column(String(12), nullable=True, unique=True)
    expires_at = Column(DateTime, nullable=False)
    redeemed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
