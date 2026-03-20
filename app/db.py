from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = "sqlite:///./gigshield.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    avg_daily_income = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("Policy", back_populates="worker")
    disruptions = relationship("DisruptionEvent", back_populates="worker")
    payouts = relationship("Payout", back_populates="worker")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
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
