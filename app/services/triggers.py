from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple


class DisruptionType:
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"


@dataclass
class TriggerRule:
    disruption_type: str
    min_severity: int
    max_hours: int
    payout_multiplier: float


DEFAULT_RULES: List[TriggerRule] = [
    TriggerRule(DisruptionType.ENVIRONMENTAL, min_severity=3, max_hours=8, payout_multiplier=0.3),
    TriggerRule(DisruptionType.SOCIAL, min_severity=2, max_hours=12, payout_multiplier=0.25),
]


class DisruptionInput:
    def __init__(
        self,
        disruption_type: str,
        severity: int,
        rainfall_mm: float,
        heat_index: float,
        aqi: int,
        flood_alert: bool,
        curfew: bool,
    ) -> None:
        self.disruption_type = disruption_type
        self.severity = severity
        self.rainfall_mm = rainfall_mm
        self.heat_index = heat_index
        self.aqi = aqi
        self.flood_alert = flood_alert
        self.curfew = curfew


def evaluate_triggers(
    inputs: DisruptionInput,
    worker_daily_income: float,
    rules: List[TriggerRule] | None = None,
) -> Tuple[bool, float]:
    if rules is None:
        rules = DEFAULT_RULES

    for rule in rules:
        if rule.disruption_type != inputs.disruption_type:
            continue
        if inputs.severity < rule.min_severity:
            continue

        disruption_intensity = 0.0
        if inputs.disruption_type == DisruptionType.ENVIRONMENTAL:
            if inputs.rainfall_mm >= 50 or inputs.heat_index >= 42 or inputs.flood_alert:
                disruption_intensity = 1.0
            elif inputs.rainfall_mm >= 20 or inputs.heat_index >= 38:
                disruption_intensity = 0.6
        else:
            if inputs.curfew:
                disruption_intensity = 1.0

        if inputs.aqi >= 300:
            disruption_intensity = max(disruption_intensity, 0.7)

        if disruption_intensity <= 0:
            continue

        fraction_of_week = min(disruption_intensity, 1.0)
        estimated_loss = worker_daily_income * 7 * fraction_of_week * rule.payout_multiplier
        return True, round(estimated_loss, 2)

    return False, 0.0
