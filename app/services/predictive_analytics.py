from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from ..schemas import Claim, ClaimStatus, Policy


CITY_RAIN_PROBABILITY = {
    "mumbai": 0.68,
    "chennai": 0.62,
    "kolkata": 0.58,
    "guwahati": 0.57,
    "kochi": 0.55,
    "delhi": 0.35,
    "bengaluru": 0.28,
    "bangalore": 0.28,
    "pune": 0.31,
    "hyderabad": 0.29,
}


def _city_rain_probability(city: str) -> float:
    if not city:
        return 0.25
    return CITY_RAIN_PROBABILITY.get(city.strip().lower(), 0.25)


def build_insurer_metrics(
    *,
    policies: List[Policy],
    claims: List[Claim],
    workers: List[dict],
) -> Dict[str, Any]:
    total_premium_collected = round(sum(float(p.weekly_premium) for p in policies), 2)

    payout_statuses = {ClaimStatus.PAID, ClaimStatus.APPROVED}
    total_payouts = round(
        sum(float(c.approved_payout) for c in claims if c.status in payout_statuses), 2
    )

    fraud_prevention_savings = round(
        sum(
            float(c.claimed_income_loss)
            for c in claims
            if c.status == ClaimStatus.REJECTED
        ),
        2,
    )

    loss_ratio = 0.0
    if total_premium_collected > 0:
        loss_ratio = round((total_payouts / total_premium_collected) * 100, 2)

    payouts = [float(c.approved_payout) for c in claims if c.status in payout_statuses]
    avg_payout = round(sum(payouts) / len(payouts), 2) if payouts else 0.0

    workers_by_city: Dict[str, int] = defaultdict(int)
    for worker in workers:
        city = str(worker.get("city") or "Unknown").strip()
        workers_by_city[city] += 1

    high_risk_zones: List[Dict[str, Any]] = []
    predicted_next_week_claims = 0

    for city, worker_count in workers_by_city.items():
        rain_probability = _city_rain_probability(city)
        expected_claims = worker_count * rain_probability * 0.45
        predicted_next_week_claims += expected_claims

        if rain_probability > 0.5:
            high_risk_zones.append(
                {
                    "city": city,
                    "rain_probability": round(rain_probability * 100, 1),
                    "expected_claims": round(expected_claims, 2),
                }
            )

    predicted_next_week_claims = round(predicted_next_week_claims, 2)
    recommended_reserve = round(predicted_next_week_claims * avg_payout, 2)

    high_risk_zones.sort(key=lambda item: item["rain_probability"], reverse=True)

    return {
        "total_premium_collected": total_premium_collected,
        "total_payouts": total_payouts,
        "fraud_prevention_savings": fraud_prevention_savings,
        "loss_ratio": loss_ratio,
        "predicted_next_week_claims": predicted_next_week_claims,
        "recommended_reserve": recommended_reserve,
        "high_risk_zones": high_risk_zones,
        "average_payout": avg_payout,
        "total_workers": len(workers),
    }
