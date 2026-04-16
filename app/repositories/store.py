from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc

from ..db import (
    ClaimRecord,
    EventRecord,
    PolicyRecord,
    RiskProfileRecord,
    SessionLocal,
    SubscriptionRecord,
    WorkerRecord,
)
from ..schemas import (
    Claim,
    ClaimStatus,
    DisruptionEvent,
    DisruptionType,
    Policy,
    RiskProfile,
)


class Store:
    def upsert_worker(self, worker: dict) -> dict:
        with SessionLocal() as db:
            record = db.get(WorkerRecord, worker["worker_id"])
            if record is None:
                record = WorkerRecord(worker_id=worker["worker_id"])
                db.add(record)

            record.name = worker["name"]
            record.city = worker["city"]
            record.pincode = worker["pincode"]
            record.platform = worker["platform"]
            record.avg_daily_income = float(worker["avg_daily_income"])
            record.experience_days = int(worker.get("experience_days", 30))
            record.joined_at = datetime.utcnow()

            db.commit()
            return {
                "worker_id": record.worker_id,
                "name": record.name,
                "city": record.city,
                "pincode": record.pincode,
                "platform": record.platform,
                "avg_daily_income": record.avg_daily_income,
                "experience_days": record.experience_days,
                "joined_at": record.joined_at.isoformat(),
            }

    def get_worker(self, worker_id: str) -> Optional[dict]:
        with SessionLocal() as db:
            record = db.get(WorkerRecord, worker_id)
            if not record:
                return None
            return {
                "worker_id": record.worker_id,
                "name": record.name,
                "city": record.city,
                "pincode": record.pincode,
                "platform": record.platform,
                "avg_daily_income": record.avg_daily_income,
                "experience_days": record.experience_days,
                "joined_at": record.joined_at.isoformat() if record.joined_at else None,
            }

    def list_workers(self) -> List[dict]:
        with SessionLocal() as db:
            records = db.query(WorkerRecord).order_by(WorkerRecord.joined_at).all()
            return [
                {
                    "worker_id": r.worker_id,
                    "name": r.name,
                    "city": r.city,
                    "pincode": r.pincode,
                    "platform": r.platform,
                    "avg_daily_income": r.avg_daily_income,
                    "experience_days": r.experience_days,
                    "joined_at": r.joined_at.isoformat() if r.joined_at else None,
                }
                for r in records
            ]

    def insert_risk(self, risk: RiskProfile) -> RiskProfile:
        with SessionLocal() as db:
            record = RiskProfileRecord(
                worker_id=risk.worker_id,
                city=risk.city,
                pincode=risk.pincode,
                avg_daily_income=risk.avg_daily_income,
                platform=risk.platform,
                risk_score=risk.risk_score,
                risk_band=risk.risk_band,
                suggested_weekly_premium=risk.suggested_weekly_premium,
                external_frequency_index=risk.external_frequency_index,
                activity_index=risk.activity_index,
            )
            db.add(record)
            db.commit()
            return risk

    def latest_risk(self, worker_id: str) -> Optional[RiskProfile]:
        with SessionLocal() as db:
            record = (
                db.query(RiskProfileRecord)
                .filter(RiskProfileRecord.worker_id == worker_id)
                .order_by(desc(RiskProfileRecord.created_at))
                .first()
            )
            if not record:
                return None
            return RiskProfile(
                worker_id=record.worker_id,
                city=record.city,
                pincode=record.pincode,
                avg_daily_income=record.avg_daily_income,
                platform=record.platform,
                risk_score=record.risk_score,
                risk_band=record.risk_band,
                suggested_weekly_premium=record.suggested_weekly_premium,
                external_frequency_index=record.external_frequency_index,
                activity_index=record.activity_index,
            )

    def list_risks(self) -> List[RiskProfile]:
        with SessionLocal() as db:
            records = db.query(RiskProfileRecord).all()
            return [
                RiskProfile(
                    worker_id=r.worker_id,
                    city=r.city,
                    pincode=r.pincode,
                    avg_daily_income=r.avg_daily_income,
                    platform=r.platform,
                    risk_score=r.risk_score,
                    risk_band=r.risk_band,
                    suggested_weekly_premium=r.suggested_weekly_premium,
                    external_frequency_index=r.external_frequency_index,
                    activity_index=r.activity_index,
                )
                for r in records
            ]

    def insert_policy(self, policy: Policy) -> Policy:
        with SessionLocal() as db:
            db.add(
                PolicyRecord(
                    policy_id=policy.policy_id,
                    worker_id=policy.worker_id,
                    weekly_premium=policy.weekly_premium,
                    coverage_per_week=policy.coverage_per_week,
                    risk_score=policy.risk_score,
                    risk_band=policy.risk_band,
                    active=bool(policy.active),
                    created_at=policy.created_at,
                )
            )
            db.commit()
            return policy

    def get_active_policy(self, worker_id: str) -> Optional[Policy]:
        with SessionLocal() as db:
            r = (
                db.query(PolicyRecord)
                .filter(
                    PolicyRecord.worker_id == worker_id, PolicyRecord.active == True
                )
                .order_by(desc(PolicyRecord.created_at))
                .first()
            )
            if not r:
                return None
            return Policy(
                policy_id=r.policy_id,
                worker_id=r.worker_id,
                weekly_premium=r.weekly_premium,
                coverage_per_week=r.coverage_per_week,
                risk_score=r.risk_score,
                risk_band=r.risk_band,
                active=r.active,
                created_at=r.created_at,
            )

    def list_policies(self) -> List[Policy]:
        with SessionLocal() as db:
            rows = db.query(PolicyRecord).order_by(PolicyRecord.created_at).all()
            return [
                Policy(
                    policy_id=r.policy_id,
                    worker_id=r.worker_id,
                    weekly_premium=r.weekly_premium,
                    coverage_per_week=r.coverage_per_week,
                    risk_score=r.risk_score,
                    risk_band=r.risk_band,
                    active=r.active,
                    created_at=r.created_at,
                )
                for r in rows
            ]

    def insert_event(self, event: DisruptionEvent) -> DisruptionEvent:
        with SessionLocal() as db:
            db.add(
                EventRecord(
                    event_id=event.event_id,
                    worker_id=event.worker_id,
                    disruption_type=event.disruption_type.value,
                    severity=event.severity,
                    description=event.description,
                    start_time=event.start_time,
                    end_time=event.end_time,
                )
            )
            db.commit()
            return event

    def list_events(self) -> List[DisruptionEvent]:
        with SessionLocal() as db:
            rows = db.query(EventRecord).order_by(EventRecord.start_time).all()
            return [
                DisruptionEvent(
                    event_id=r.event_id,
                    worker_id=r.worker_id,
                    disruption_type=DisruptionType(r.disruption_type),
                    severity=r.severity,
                    description=r.description,
                    start_time=r.start_time,
                    end_time=r.end_time,
                )
                for r in rows
            ]

    def insert_claim(self, claim: Claim) -> Claim:
        with SessionLocal() as db:
            db.add(
                ClaimRecord(
                    claim_id=claim.claim_id,
                    worker_id=claim.worker_id,
                    policy_id=claim.policy_id,
                    event_id=claim.event_id,
                    claimed_income_loss=claim.claimed_income_loss,
                    approved_payout=claim.approved_payout,
                    status=claim.status.value,
                    created_at=claim.created_at,
                )
            )
            db.commit()
            return claim

    def update_claim(self, claim: Claim) -> None:
        with SessionLocal() as db:
            record = db.get(ClaimRecord, claim.claim_id)
            if not record:
                return
            record.approved_payout = claim.approved_payout
            record.status = claim.status.value
            db.commit()

    def list_claims(self) -> List[Claim]:
        with SessionLocal() as db:
            rows = db.query(ClaimRecord).order_by(ClaimRecord.created_at).all()
            return [
                Claim(
                    claim_id=r.claim_id,
                    worker_id=r.worker_id,
                    policy_id=r.policy_id,
                    event_id=r.event_id,
                    claimed_income_loss=r.claimed_income_loss,
                    approved_payout=r.approved_payout,
                    status=ClaimStatus(r.status),
                    created_at=r.created_at,
                )
                for r in rows
            ]

    def add_subscription(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as db:
            record = SubscriptionRecord(
                id=item["id"],
                created_at=datetime.fromisoformat(item["created_at"]),
                customer_name=item["customer_name"],
                customer_email=item["customer_email"],
                plan_id=item["plan_id"],
                plan_name=item["plan_name"],
                amount_paise=int(item["amount_paise"]),
                currency=item["currency"],
                order_id=item["order_id"],
                payment_id=item.get("payment_id"),
                status=item["status"],
                mode=item["mode"],
            )
            db.add(record)
            db.commit()
            return item

    def update_subscription_by_order(
        self,
        order_id: str,
        *,
        status: Optional[str] = None,
        payment_id: Optional[str] = None,
        verified_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        with SessionLocal() as db:
            record = (
                db.query(SubscriptionRecord)
                .filter(SubscriptionRecord.order_id == order_id)
                .order_by(desc(SubscriptionRecord.created_at))
                .first()
            )
            if not record:
                return None
            if status is not None:
                record.status = status
            if payment_id is not None:
                record.payment_id = payment_id
            if verified_at is not None:
                record.verified_at = verified_at
            db.commit()
            return self._sub_dict(record)

    def latest_subscription_by_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as db:
            record = (
                db.query(SubscriptionRecord)
                .filter(SubscriptionRecord.order_id == order_id)
                .order_by(desc(SubscriptionRecord.created_at))
                .first()
            )
            if not record:
                return None
            return self._sub_dict(record)

    def list_subscriptions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            query = db.query(SubscriptionRecord)
            if status:
                query = query.filter(SubscriptionRecord.status == status)
            rows = query.order_by(SubscriptionRecord.created_at).all()
            return [self._sub_dict(r) for r in rows]

    def list_subscriptions_for_email(self, customer_email: str) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(SubscriptionRecord)
                .filter(SubscriptionRecord.customer_email.ilike(customer_email))
                .order_by(SubscriptionRecord.created_at)
                .all()
            )
            return [self._sub_dict(r) for r in rows]

    @staticmethod
    def _sub_dict(record: SubscriptionRecord) -> Dict[str, Any]:
        return {
            "id": record.id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "customer_name": record.customer_name,
            "customer_email": record.customer_email,
            "plan_id": record.plan_id,
            "plan_name": record.plan_name,
            "amount_paise": record.amount_paise,
            "currency": record.currency,
            "order_id": record.order_id,
            "payment_id": record.payment_id,
            "status": record.status,
            "mode": record.mode,
            "verified_at": record.verified_at.isoformat()
            if record.verified_at
            else None,
        }


store = Store()
