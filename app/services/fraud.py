from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

from ..schemas import Claim


@dataclass
class FraudSignal:
    code: str
    message: str
    severity: int


class FraudEngine:
    def __init__(self) -> None:
        self.claims_by_worker: Dict[str, List[Claim]] = defaultdict(list)

    def evaluate_claim(self, claim: Claim) -> List[FraudSignal]:
        signals: List[FraudSignal] = []

        worker_claims = self.claims_by_worker[claim.worker_id]
        now = datetime.utcnow()
        recent = [c for c in worker_claims if now - c.created_at <= timedelta(days=7)]
        if len(recent) >= 2:
            signals.append(
                FraudSignal(
                    code="FREQUENT_CLAIMS",
                    message="Multiple claims in last 7 days",
                    severity=3,
                )
            )

        duplicate = next(
            (
                c
                for c in worker_claims
                if c.event_id == claim.event_id and c.claim_id != claim.claim_id
            ),
            None,
        )
        if duplicate:
            signals.append(
                FraudSignal(
                    code="DUPLICATE_EVENT",
                    message="Claim already exists for this disruption event",
                    severity=4,
                )
            )

        if claim.claimed_income_loss > 2.5 * claim.approved_payout:
            signals.append(
                FraudSignal(
                    code="INFLATED_LOSS",
                    message="Claimed loss far exceeds model payout",
                    severity=2,
                )
            )

        self.claims_by_worker[claim.worker_id].append(claim)

        return signals
