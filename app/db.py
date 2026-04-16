from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def _resolve_database_url() -> str:
    raw = os.getenv("DATABASE_URL", "sqlite:///./gigshield.db").strip()

    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql://", 1)

    if raw.startswith("http://") or raw.startswith("https://"):
        return "sqlite:///./gigshield.db"

    return raw


DATABASE_URL = _resolve_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class WorkerRecord(Base):
    __tablename__ = "gw_workers"

    worker_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    pincode: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    avg_daily_income: Mapped[float] = mapped_column(Float, nullable=False)
    experience_days: Mapped[int] = mapped_column(Integer, default=30)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskProfileRecord(Base):
    __tablename__ = "gw_risk_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    pincode: Mapped[str | None] = mapped_column(Text, nullable=True)
    avg_daily_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    platform: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False)
    suggested_weekly_premium: Mapped[float] = mapped_column(Float, nullable=False)
    external_frequency_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PolicyRecord(Base):
    __tablename__ = "gw_policies"

    policy_id: Mapped[str] = mapped_column(Text, primary_key=True)
    worker_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    weekly_premium: Mapped[float] = mapped_column(Float, nullable=False)
    coverage_per_week: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EventRecord(Base):
    __tablename__ = "gw_events"

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    worker_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    disruption_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ClaimRecord(Base):
    __tablename__ = "gw_claims"

    claim_id: Mapped[str] = mapped_column(Text, primary_key=True)
    worker_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    policy_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    event_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    claimed_income_loss: Mapped[float] = mapped_column(Float, nullable=False)
    approved_payout: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SubscriptionRecord(Base):
    __tablename__ = "gw_subscriptions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    customer_email: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(Text, nullable=False)
    plan_name: Mapped[str] = mapped_column(Text, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    order_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    payment_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
