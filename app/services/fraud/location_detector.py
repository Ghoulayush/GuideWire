"""
Lightweight Location Spoofing Detector.

This module provides a CPU-friendly heuristic-first implementation that
flags impossible speeds and GPS teleportation. If a more advanced LSTM
autoencoder is desired later, the class can be extended to load/train
one when `tensorflow` is available.
"""
from dataclasses import dataclass
from datetime import datetime
import math
from typing import List, Dict, Any
from statistics import mean
import numpy as np
from sklearn.cluster import DBSCAN


def _haversine_km(lat1, lon1, lat2, lon2):
    # approximate distance in km between two lat/lon points
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


@dataclass
class LocationSpoofResult:
    speed_anomaly_score: float
    teleportation_score: float
    reconstruction_error: float
    fraud_score: float
    details: Dict[str, Any]


class LocationSpoofingDetector:
    """Detects unlikely movement patterns.

    Input: list of points: [{'lat':..., 'lon':..., 'ts': 167...}, ...]
    ts may be epoch seconds (int/float) or ISO string (will try parse).
    """

    def __init__(self, max_speed_kmh: float = 60.0, teleport_km: float = 5.0, teleport_sec: int = 60):
        self.max_speed_kmh = max_speed_kmh
        self.teleport_km = teleport_km
        self.teleport_sec = teleport_sec

    def _parse_ts(self, ts):
        if isinstance(ts, (int, float)):
            return float(ts)
        try:
            # ISO format
            return datetime.fromisoformat(ts).timestamp()
        except Exception:
            return float(ts)

    def evaluate(self, points: List[Dict[str, Any]]) -> LocationSpoofResult:
        if not points or len(points) < 2:
            return LocationSpoofResult(0.0, 0.0, 0.0, 0.0, {"n_points": len(points)})

        speed_violations = 0
        teleport_violations = 0
        total_pairs = 0
        disps = []
        times = []

        prev = points[0]
        prev_t = self._parse_ts(prev.get("ts", datetime.utcnow().timestamp()))

        for cur in points[1:]:
            cur_t = self._parse_ts(cur.get("ts", datetime.utcnow().timestamp()))
            dt = cur_t - prev_t
            if dt <= 0:
                prev = cur
                prev_t = cur_t
                continue

            dist = _haversine_km(prev["lat"], prev["lon"], cur["lat"], cur["lon"])
            speed = (dist / (dt / 3600.0)) if dt > 0 else 0.0

            disps.append(dist)
            times.append(dt)

            if speed > self.max_speed_kmh:
                speed_violations += 1

            if dist > self.teleport_km and dt < self.teleport_sec:
                teleport_violations += 1

            total_pairs += 1
            prev = cur
            prev_t = cur_t

        avg_speed = mean([d / (t/3600.0) for d, t in zip(disps, times)]) if disps else 0.0
        max_speed = max([d / (t/3600.0) for d, t in zip(disps, times)]) if disps else 0.0
        std_disp = float(np.std(disps)) if disps else 0.0

        # DBSCAN cluster density to spot many locations
        coords = np.array([[p["lat"], p["lon"]] for p in points])
        try:
            db = DBSCAN(eps=0.01, min_samples=3).fit(coords)
            labels = db.labels_
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        except Exception:
            n_clusters = 0

        speed_score = min(100.0, speed_violations * 30.0)
        teleport_score = min(100.0, teleport_violations * 40.0)
        recon_error = 0.0

        combined = min(100.0, speed_score + teleport_score + std_disp * 10 + n_clusters * 5 + recon_error)

        return LocationSpoofResult(
            speed_anomaly_score=speed_score,
            teleportation_score=teleport_score,
            reconstruction_error=recon_error,
            fraud_score=combined,
            details={"n_points": len(points), "pairs_checked": total_pairs, "std_disp": std_disp, "clusters": n_clusters},
        )
