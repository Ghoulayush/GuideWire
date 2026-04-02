"""
IsolationForest-based location anomaly detector.

Extracts simple trajectory features (avg speed, max speed, teleport_count,
std of displacements) and fits an IsolationForest on synthetic normal data.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
import math
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


@dataclass
class LocationIsolationResult:
    anomaly_score: float
    details: Dict[str, Any]


class LocationIsolationDetector:
    def __init__(self, model_path: str = 'models/location_isolation.pkl'):
        self.model_path = model_path
        self.model = None
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
            except Exception:
                self.model = None

    def _trajectory_features(self, points: List[Dict[str, Any]]):
        if not points or len(points) < 2:
            return [0.0, 0.0, 0.0, 0.0]
        times = []
        dists = []
        prev = points[0]
        prev_t = float(prev.get('ts', 0))
        for cur in points[1:]:
            cur_t = float(cur.get('ts', prev_t + 60))
            dt = max(1.0, cur_t - prev_t)
            dist = _haversine_km(prev['lat'], prev['lon'], cur['lat'], cur['lon'])
            speed = dist / (dt / 3600.0)
            dists.append(dist)
            times.append(dt)
            prev = cur
            prev_t = cur_t

        avg_speed = sum(dists) / len(dists) * 3600.0 / (sum(times) / len(times)) if dists else 0.0
        max_speed = max([ (d / (t/3600.0)) for d,t in zip(dists,times) ]) if dists else 0.0
        teleports = sum(1 for d in dists if d > 5.0)
        std_dist = float(np.std(dists)) if dists else 0.0
        return [avg_speed, max_speed, teleports, std_dist]

    def fit_on_synthetic(self, n=2000):
        # Build synthetic normal trajectories (random walk)
        X = []
        for _ in range(n):
            lat = 19.0 + np.random.normal(0, 0.01)
            lon = 72.8 + np.random.normal(0, 0.01)
            points = []
            t = 0
            for _ in range(24):
                lat += np.random.normal(0, 0.002)
                lon += np.random.normal(0, 0.002)
                points.append({'lat': float(lat), 'lon': float(lon), 'ts': float(t)})
                t += 300
            X.append(self._trajectory_features(points))

        X = np.array(X)
        model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
        model.fit(X)
        self.model = model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)

    def detect(self, points: List[Dict[str, Any]]) -> LocationIsolationResult:
        feat = self._trajectory_features(points)
        details = {'features': feat}
        if self.model is None:
            # higher score for unusual heuristics
            score = min(100.0, feat[2] * 40 + feat[1] / 2.0)
            return LocationIsolationResult(anomaly_score=score, details=details)

        import numpy as _np
        score_raw = -self.model.score_samples([feat])[0]  # higher means more anomalous
        # normalize roughly to 0-100
        score = float(min(100.0, max(0.0, score_raw * 25.0)))
        return LocationIsolationResult(anomaly_score=score, details=details)
