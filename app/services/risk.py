from __future__ import annotations

from dataclasses import dataclass


from ..schemas import RiskProfile


@dataclass
class RiskWeights:
    age_weight: float = 0.15
    orders_weight: float = -0.1
    earnings_weight: float = -0.05
    cancellations_weight: float = 0.4
    city_risk_weight: float = 0.2


CITY_RISK = {
    "high": {"mumbai", "delhi", "kolkata", "chennai", "bangalore"},
    "medium": {"pune", "hyderabad", "ahmedabad", "jaipur"},
}


@dataclass
class RiskInput:
    city: str
    pincode: str
    avg_daily_income: float
    platform: str
    external_frequency_index: float
    activity_index: float


def _city_risk_factor(city: str) -> float:
    c = city.strip().lower()
    if c in CITY_RISK["high"]:
        return 1.0
    if c in CITY_RISK["medium"]:
        return 0.6
    return 0.3


def calculate_risk(risk_in: RiskInput, weights: RiskWeights | None = None) -> RiskProfile:
    if weights is None:
        weights = RiskWeights()

    norm_income = min(risk_in.avg_daily_income / 2000, 1)
    city_factor = _city_risk_factor(risk_in.city)

    norm_external = risk_in.external_frequency_index
    norm_activity = risk_in.activity_index

    raw_score = (
        weights.earnings_weight * (1 - norm_income)
        + weights.city_risk_weight * city_factor
        + 0.3 * norm_external
        + 0.2 * norm_activity
    )

    risk_score = 1 / (1 + pow(2.718, -5 * (raw_score - 0.3)))
    risk_score = max(0.0, min(1.0, risk_score))

    score_0_100 = max(0.0, min(100.0, risk_score * 100))

    if score_0_100 < 33:
        band = "low"
        premium_factor = 0.04
    elif score_0_100 < 66:
        band = "medium"
        premium_factor = 0.06
    else:
        band = "high"
        premium_factor = 0.08

    suggested_premium = risk_in.avg_daily_income * 7 * premium_factor

    return RiskProfile(
        worker_id="",
        risk_score=round(score_0_100, 1),
        risk_band=band,
        suggested_weekly_premium=round(suggested_premium, 2),
    )
