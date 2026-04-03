from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gigshield.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Worker(Base):
    __tablename__ = "workers"

    worker_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    pincode = Column(Text)
    platform = Column(Text)
    avg_daily_income = Column(Float)
    experience_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("Policy", back_populates="worker")
    claims = relationship("Claim", back_populates="worker")
    disruption_events = relationship("DisruptionEvent", back_populates="worker")


class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Text, primary_key=True)
    worker_id = Column(Text, ForeignKey("workers.worker_id"))
    weekly_premium = Column(Float)
    coverage_per_week = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Text, primary_key=True)
    worker_id = Column(Text, ForeignKey("workers.worker_id"))
    policy_id = Column(Text, ForeignKey("policies.policy_id"))
    event_id = Column(Text)
    claimed_amount = Column(Float)
    approved_payout = Column(Float)
    status = Column(Text, default='PENDING')
    fraud_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="claims")
    policy = relationship("Policy", back_populates="claims")


class DisruptionEvent(Base):
    __tablename__ = "disruption_events"

    event_id = Column(Text, primary_key=True)
    worker_id = Column(Text, ForeignKey("workers.worker_id"))
    disruption_type = Column(Text)
    severity = Column(Integer)
    description = Column(Text)
    triggered = Column(Boolean, default=False)
    payout_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="disruption_events")


# Create tables
Base.metadata.create_all(bind=engine)

    weekly_premium = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_band = Column(String, nullable=False)
    coverage_per_week = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="policies")


class DisruptionEvent(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    disruption_type = Column(String, nullable=False)
    severity = Column(Integer, nullable=False)
    rainfall_mm = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    heat_index = Column(Float, nullable=True)
    aqi = Column(Integer, nullable=True)
    flood_alert = Column(Boolean, default=False)
    curfew = Column(Boolean, default=False)
    source = Column(String, default="simulated")
    description = Column(String, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="disruptions")
    payouts = relationship("Payout", back_populates="event")


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    policy_id = Column(Integer, ForeignKey("policies.id"))
    event_id = Column(Integer, ForeignKey("disruptions.id"))
    amount = Column(Float, nullable=False)
    status = Column(String, default="approved")
    fraud_flag = Column(Boolean, default=False)
    fraud_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="payouts")
    policy = relationship("Policy")
    event = relationship("DisruptionEvent", back_populates="payouts")


def init_db() -> None:
    from . import models  # noqa: F401  # ensure pydantic models imported if needed

    Base.metadata.create_all(bind=engine)
