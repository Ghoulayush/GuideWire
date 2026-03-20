from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExternalSignals:
    rainfall_mm: float
    temperature_c: float
    heat_index: float
    aqi: int
    flood_alert: bool
    curfew: bool


def _mock_signals(city: str, pincode: str) -> ExternalSignals:
    base_aqi = 80 if city.lower() in {"bangalore", "pune"} else 150
    return ExternalSignals(
        rainfall_mm=random.choice([0, 5, 20, 60]),
        temperature_c=random.uniform(26, 42),
        heat_index=random.uniform(28, 50),
        aqi=int(base_aqi + random.randint(-20, 80)),
        flood_alert=random.random() < 0.2,
        curfew=random.random() < 0.1,
    )


def fetch_signals(
    city: str,
    pincode: str,
    *,
    use_live: bool = False,
    weather_api_key: Optional[str] = None,
    aqi_api_key: Optional[str] = None,
) -> ExternalSignals:
    """Return external disruption signals.

    For hackathon use, this defaults to mocked data but the signature
    is ready for plugging real weather / AQI / civic alert APIs.
    """

    # TODO: plug real APIs when keys are available.
    return _mock_signals(city, pincode)
