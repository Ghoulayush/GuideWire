"""
Collusion ring detector using DBSCAN clustering on location + temporal checks.

Uses scikit-learn's DBSCAN with a precomputed haversine distance matrix.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
import math
import numpy as np
from sklearn.cluster import DBSCAN
from .base_detector import standardize_result


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


@dataclass
class CollusionResult:
    clusters: List[Dict[str, Any]]
    fraud_score: float


class CollusionRingDetector:
    def __init__(self, eps_km: float = 0.5, min_samples: int = 5, time_window_sec: int = 3600):
        self.eps_km = eps_km
        self.min_samples = min_samples
        self.time_window_sec = time_window_sec

    def _build_distance_matrix(self, coords: List[List[float]]) -> np.ndarray:
        n = len(coords)
        if n == 0:
            return np.zeros((0, 0))
        mat = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(i + 1, n):
                d = _haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                mat[i, j] = d
                mat[j, i] = d
        return mat

    def analyze_claims(self, claims: List[Dict[str, Any]]) -> CollusionResult:
        """claims: list of {'lat':..., 'lon':..., 'timestamp': epoch_seconds, 'claim_id':..., 'disruption_type':...}
        """
        if not claims:
            return CollusionResult(clusters=[], fraud_score=0.0)

        coords = [[c['lat'], c['lon']] for c in claims]
        dist_mat = self._build_distance_matrix(coords)

        if dist_mat.size == 0:
            return CollusionResult(clusters=[], fraud_score=0.0)

        db = DBSCAN(eps=self.eps_km, min_samples=1, metric='precomputed')
        labels = db.fit_predict(dist_mat)

        clusters = {}
        for idx, label in enumerate(labels):
            clusters.setdefault(label, []).append((idx, claims[idx]))

        results = []
        total_fraud_score = 0.0
        for label, members in clusters.items():
            if label == -1:
                continue
            indices, members_claims = zip(*members)
            times = [c['timestamp'] for c in members_claims]
            min_t = min(times)
            max_t = max(times)
            duration = max_t - min_t
            size = len(members_claims)

            suspicious = size >= self.min_samples and duration <= self.time_window_sec
            score = 0.0
            if suspicious:
                score = min(100.0, 50.0 + (size - self.min_samples) * 10.0)
            else:
                # weaker signal if many claims but over longer time
                if size >= self.min_samples:
                    score = 30.0

            total_fraud_score = max(total_fraud_score, score)

            results.append({
                'label': int(label),
                'size': size,
                'duration_sec': duration,
                'suspicious': suspicious,
                'score': score,
                'indices': list(indices),
            })

        return CollusionResult(clusters=results, fraud_score=total_fraud_score)

    def detect_rings(self, claims: List[Dict[str, Any]]):
        """Return standardized FraudResult for collusion analysis."""
        coll_res = self.analyze_claims(claims)

        fraud_score = int(coll_res.fraud_score)
        if fraud_score >= 70:
            action = "REJECT"
        elif fraud_score >= 40:
            action = "REVIEW"
        else:
            action = "APPROVE"

        raw = {
            "fraud_score": fraud_score,
            "action": action,
            "reason": f"Detected {len(coll_res.clusters)} clusters, top_score={fraud_score}",
            "confidence": int(min(100, max(0, fraud_score if fraud_score else 50))),
            "metadata": {"clusters": coll_res.clusters},
        }

        return standardize_result(raw, "CollusionRingDetector")
