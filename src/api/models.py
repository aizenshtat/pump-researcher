"""SQLAlchemy models for the database."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Pump(Base):
    __tablename__ = "pumps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    price_change_pct = Column(Float, nullable=False)
    time_window_minutes = Column(Integer, default=60)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    price_at_detection = Column(Float)
    volume_change_pct = Column(Float)
    market_cap = Column(Float)
    source = Column(String(50), default="coinmarketcap")

    # Relationships
    findings = relationship("Finding", back_populates="pump", cascade="all, delete-orphan")
    trigger = relationship("NewsTrigger", back_populates="pump", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="pump", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pump_id = Column(Integer, ForeignKey("pumps.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    source_url = Column(Text)
    content = Column(Text)
    relevance_score = Column(Float, default=0.5)
    sentiment = Column(String(20), default="neutral")
    found_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pump = relationship("Pump", back_populates="findings")


class NewsTrigger(Base):
    __tablename__ = "news_triggers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pump_id = Column(Integer, ForeignKey("pumps.id"), nullable=False, unique=True, index=True)
    trigger_type = Column(String(50), nullable=False)
    description = Column(Text)
    confidence = Column(Float, default=0.5)
    identified_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pump = relationship("Pump", back_populates="trigger")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pump_id = Column(Integer, ForeignKey("pumps.id"), nullable=False)
    channel = Column(String(50), default="telegram")
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")

    # Relationships
    pump = relationship("Pump", back_populates="notifications")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    pumps_detected = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)
    status = Column(String(20), default="running")
    error_message = Column(Text)
    logs = Column(Text)
