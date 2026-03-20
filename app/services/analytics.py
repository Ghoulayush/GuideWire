from __future__ import annotations

from typing import List

from ..schemas import AnalyticsMetrics, Claim, ClaimStatus, DisruptionEvent, Policy, RiskProfile


def build_metrics(
    risks: List[RiskProfile],
    policies: List[Policy],
    claims: List[Claim],
    events: List[DisruptionEvent],
) -> AnalyticsMetrics:
    total_workers = len({r.worker_id for r in risks})
    active_policies = len(policies)
    total_claims = len(claims)
    approved_claims = len([c for c in claims if c.status == ClaimStatus.APPROVED])
    total_payout = sum(c.approved_payout for c in claims)
    avg_risk = sum(r.risk_score for r in risks) / total_workers if total_workers else 0.0

    disruption_counts = []
    by_type = {}
    for e in events:
        key = e.disruption_type.value
        by_type[key] = by_type.get(key, 0) + 1
    for k, v in by_type.items():
        disruption_counts.append({"type": k, "count": v})

    return AnalyticsMetrics(
        total_workers=total_workers,
        active_policies=active_policies,
        total_claims=total_claims,
        approved_claims=approved_claims,
        total_payout=round(total_payout, 2),
        avg_risk_score=round(avg_risk, 3),
        disruption_counts=disruption_counts,
    )
