"""SQLAlchemy models for the database."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Pump(db.Model):
    __tablename__ = "pumps"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    price_change_pct = db.Column(db.Float, nullable=False)
    time_window_minutes = db.Column(db.Integer, default=60)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    price_at_detection = db.Column(db.Float)
    volume_change_pct = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    source = db.Column(db.String(50), default="coinmarketcap")

    # Relationships
    findings = db.relationship("Finding", back_populates="pump", cascade="all, delete-orphan")
    trigger = db.relationship("NewsTrigger", back_populates="pump", uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="pump", cascade="all, delete-orphan")


class Finding(db.Model):
    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pump_id = db.Column(db.Integer, db.ForeignKey("pumps.id"), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False, index=True)
    source_url = db.Column(db.Text)
    content = db.Column(db.Text)
    relevance_score = db.Column(db.Float, default=0.5)
    sentiment = db.Column(db.String(20), default="neutral")
    found_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pump = db.relationship("Pump", back_populates="findings")


class NewsTrigger(db.Model):
    __tablename__ = "news_triggers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pump_id = db.Column(db.Integer, db.ForeignKey("pumps.id"), nullable=False, unique=True, index=True)
    trigger_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    confidence = db.Column(db.Float, default=0.5)
    identified_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pump = db.relationship("Pump", back_populates="trigger")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pump_id = db.Column(db.Integer, db.ForeignKey("pumps.id"), nullable=False)
    channel = db.Column(db.String(50), default="telegram")
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="sent")

    # Relationships
    pump = db.relationship("Pump", back_populates="notifications")


class AgentRun(db.Model):
    __tablename__ = "agent_runs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    pumps_detected = db.Column(db.Integer, default=0)
    findings_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="running")
    error_message = db.Column(db.Text)
    logs = db.Column(db.Text)
