from __future__ import annotations

from datetime import datetime
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, List


def _to_epoch(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).timestamp()
        except Exception:
            return None
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return radius * (2 * atan2(sqrt(a), sqrt(1 - a)))


def detect_advanced_signals(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []

    gps_history = claim_data.get("gps_history") or claim_data.get("trajectory") or []
    if isinstance(gps_history, list) and len(gps_history) >= 2:
        for i in range(1, len(gps_history)):
            prev = gps_history[i - 1]
            curr = gps_history[i]

            try:
                dist_km = _haversine_km(
                    float(prev["lat"]),
                    float(prev["lon"]),
                    float(curr["lat"]),
                    float(curr["lon"]),
                )
            except Exception:
                continue

            prev_ts = _to_epoch(prev.get("ts") or prev.get("timestamp"))
            curr_ts = _to_epoch(curr.get("ts") or curr.get("timestamp"))
            if prev_ts is None or curr_ts is None:
                continue

            dt_hours = max((curr_ts - prev_ts) / 3600.0, 1e-6)
            speed = dist_km / dt_hours

            if speed > 60:
                score += 20
                reasons.append(f"Impossible movement speed detected ({speed:.1f} km/h)")

            dt_minutes = max((curr_ts - prev_ts) / 60.0, 0.0)
            if dist_km > 10 and dt_minutes < 5:
                score += 25
                reasons.append(
                    f"Teleportation pattern detected ({dist_km:.1f} km in {dt_minutes:.1f} min)"
                )

    weather_claimed = claim_data.get("claimed_weather", {}) or {}
    weather_actual = claim_data.get("actual_weather", {}) or {}
    claimed_rain = float(weather_claimed.get("rain_mm", 0) or 0)
    actual_rain = float(weather_actual.get("rain_mm", 0) or 0)
    if claimed_rain >= 40 and actual_rain <= 5:
        score += 25
        reasons.append(
            f"Claimed heavy rain ({claimed_rain:.0f}mm) mismatches actual weather ({actual_rain:.0f}mm)"
        )

    claims_in_area = claim_data.get("claims_in_area") or []
    if isinstance(claims_in_area, list) and len(claims_in_area) >= 5:
        timestamps = []
        for entry in claims_in_area:
            ts = _to_epoch(entry.get("timestamp") or entry.get("ts"))
            if ts is not None:
                timestamps.append(ts)
        if timestamps:
            if max(timestamps) - min(timestamps) <= 3600:
                score += 20
                reasons.append(
                    "Potential collusion ring: 5+ claims in same area within 1 hour"
                )

    historical = claim_data.get("historical_validation") or {}
    historical_ok = bool(historical.get("matches_pattern", True))
    if not historical_ok:
        score += 10
        reasons.append("Claim does not match historical behavior pattern")

    score = min(score, 100)
    if score >= 70:
        action = "REJECT"
    elif score >= 40:
        action = "REVIEW"
    else:
        action = "APPROVE"

    return {
        "fraud_score": score,
        "action": action,
        "reason": " | ".join(reasons) if reasons else "Advanced checks found no issues",
        "confidence": 80 if score > 0 else 90,
        "detector_name": "AdvancedFraudDetector",
        "metadata": {"signals": reasons},
    }
