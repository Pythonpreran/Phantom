"""
PHANTOM — Database Models & Setup (SQLAlchemy + SQLite)
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phantom.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user, company, admin
    company_name = Column(String(255), nullable=True)
    company_id = Column(String(50), nullable=True)  # "abc", "xyz", or None for admin
    is_blocked = Column(Boolean, default=False)
    simulated_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), index=True)
    endpoint = Column(String(500))
    method = Column(String(10))
    status_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    response_time_ms = Column(Float)
    user_agent = Column(String(500))
    attempt_count = Column(Integer, default=1)
    prediction = Column(String(20))
    confidence = Column(Float)
    attack_type = Column(String(100))
    company_id = Column(String(100), default="xyz")
    user_id = Column(Integer, nullable=True)


class BlockedIP(Base):
    __tablename__ = "blocked_ips"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, index=True)
    reason = Column(String(500))
    attack_type = Column(String(100))
    confidence = Column(Float)
    blocked_at = Column(DateTime, default=datetime.utcnow)
    blocked_by = Column(String(50), default="system")
    is_active = Column(Boolean, default=True)
    flagged = Column(Boolean, default=False)
    company_id = Column(String(50), nullable=True)  # which company's user triggered this


class HoneypotEvent(Base):
    __tablename__ = "honeypot_events"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), index=True)
    endpoint = Column(String(500))
    method = Column(String(10))
    payload = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50))
    captured_data = Column(Text)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String(20))
    title = Column(String(500))
    description = Column(Text)
    ip_address = Column(String(45))
    attack_type = Column(String(100))
    action_taken = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    company_id = Column(String(100), default="xyz")


class ValidationTest(Base):
    __tablename__ = "validation_tests"
    id = Column(Integer, primary_key=True, index=True)
    test_type = Column(String(50))
    status = Column(String(20), default="running")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0)
    detected_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    avg_detection_time_ms = Column(Float, default=0)
    results_json = Column(Text)
    company_id = Column(String(100), default="xyz")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
