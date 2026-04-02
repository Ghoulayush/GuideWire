from __future__ import annotations

"""Fraud detection package helpers and ensemble.

Provides a high-level `FraudEngine` that orchestrates lightweight
detectors (location, collusion, image) and optional advanced detectors
when available. The engine emits `FraudSignal` items used by the app.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.schemas import Claim

from .location_detector import LocationSpoofingDetector
from .collusion_detector import CollusionRingDetector
from .image_detector import ImageFraudDetector

# Optional detectors
try:
    from .location_isolation import LocationIsolationDetector
except Exception:
    LocationIsolationDetector = None

try:
    from .location_autoencoder import LocationAutoencoder
except Exception:
    LocationAutoencoder = None

try:
    from .image_cnn import ImageCNNDetector
except Exception:
    ImageCNNDetector = None

# Optional ensemble
try:
    from .ensemble import FraudEnsemble
except Exception:
    FraudEnsemble = None


@dataclass
class FraudSignal:
    code: str
    message: str
    severity: int


class FraudEngine:
    """High-level fraud orchestrator that keeps per-worker claim history
    and applies a set of detectors to flag suspicious claims.
    """

    def __init__(self, model_dir: str = "models") -> None:
        self.claims_by_worker: Dict[str, List[Claim]] = defaultdict(list)
        self.location_detector = LocationSpoofingDetector()
        self.collusion_detector = CollusionRingDetector()
        self.image_detector = ImageFraudDetector()
        self.location_isolation: Optional[object] = None

        if LocationIsolationDetector is not None:
            try:
                self.location_isolation = LocationIsolationDetector(model_path=f"{model_dir}/location_isolation.pkl")
            except Exception:
                self.location_isolation = None

        self.location_autoenc = LocationAutoencoder() if LocationAutoencoder else None
        self.image_cnn = ImageCNNDetector() if ImageCNNDetector else None
        self.ensemble = None
        if FraudEnsemble is not None:
            try:
                self.ensemble = FraudEnsemble(model_path=f"{model_dir}/fraud_ensemble.pkl")
            except Exception:
                self.ensemble = None

    def evaluate_claim(self, claim: Claim) -> List[FraudSignal]:
        signals: List[FraudSignal] = []

        worker_claims = self.claims_by_worker[claim.worker_id]
        now = datetime.utcnow()
        recent = [c for c in worker_claims if now - c.created_at <= timedelta(days=7)]
        if len(recent) >= 2:
            signals.append(FraudSignal(code="FREQUENT_CLAIMS", message="Multiple claims in last 7 days", severity=3))

        duplicate = next((c for c in worker_claims if c.event_id == claim.event_id and c.claim_id != claim.claim_id), None)
        if duplicate:
            signals.append(FraudSignal(code="DUPLICATE_EVENT", message="Claim already exists for this disruption event", severity=4))

        if claim.claimed_income_loss > 2.5 * claim.approved_payout:
            signals.append(FraudSignal(code="INFLATED_LOSS", message="Claimed loss far exceeds model payout", severity=2))

        # Try location-based detectors if trajectory available
        try:
            traj = getattr(claim, "trajectory", None) or claim.__dict__.get("trajectory")
            if traj and len(traj) >= 2:
                loc_res = self.location_detector.evaluate(traj)
                if getattr(loc_res, "fraud_score", 0) >= 50:
                    severity = 4 if loc_res.fraud_score > 80 else 3
                    signals.append(FraudSignal(code="LOCATION_ANOMALY", message=f"Location anomaly score {loc_res.fraud_score:.1f}", severity=severity))
                if self.location_isolation is not None:
                    iso_res = self.location_isolation.detect(traj)
                    if getattr(iso_res, "anomaly_score", 0) > 50:
                        signals.append(FraudSignal(code="LOCATION_ISOLATION", message=f"Isolation anomaly {iso_res.anomaly_score:.1f}", severity=3))
        except Exception:
            pass

        # Collusion detector (if claims/events info present)
        try:
            events = claim.__dict__.get("events") or []
            if events:
                coll_res = self.collusion_detector.analyze_claims(events)
                if getattr(coll_res, "fraud_score", 0) > 0:
                    signals.append(FraudSignal(code="COLLUSION", message=f"Collusion cluster detected score {coll_res.fraud_score:.1f}", severity=3))
        except Exception:
            pass

        # Image analysis
        try:
            images = getattr(claim, "images", None) or claim.__dict__.get("images", [])
            for image in images or []:
                img_res = self.image_detector.analyze(image)
                if getattr(img_res, "fake_probability", 0) > 0.5:
                    signals.append(FraudSignal(code="IMAGE_FRAUD", message=f"Image flagged fake probability {img_res.fake_probability:.2f}", severity=4))
        except Exception:
            pass

        # append to history
        self.claims_by_worker[claim.worker_id].append(claim)

        # Ensemble-level scoring (if available)
        try:
            if self.ensemble is not None:
                features = {
                    'location_score': getattr(loc_res, 'fraud_score', 0) if 'loc_res' in locals() else 0,
                    'collusion_score': getattr(coll_res, 'fraud_score', 0) if 'coll_res' in locals() else 0,
                    'image_prob': max([getattr(img_res, 'fake_probability', 0) for img_res in ([img_res] if 'img_res' in locals() else [])]) if 'img_res' in locals() else 0,
                    'isolation_score': getattr(iso_res, 'anomaly_score', 0) if 'iso_res' in locals() else 0,
                    'claimed_ratio': (claim.claimed_income_loss / max(1.0, claim.approved_payout)) if claim.approved_payout else claim.claimed_income_loss,
                    'event_count': len(claim.__dict__.get('events') or []),
                }
                prob = self.ensemble.predict_proba(features)
                if prob >= 0.6:
                    signals.append(FraudSignal(code='ENSEMBLE_FRAUD', message=f'Ensemble fraud probability {prob:.2f}', severity=4))
                elif prob >= 0.4:
                    signals.append(FraudSignal(code='ENSEMBLE_SUSPICIOUS', message=f'Ensemble suspicious probability {prob:.2f}', severity=3))
        except Exception:
            pass

        return signals


__all__ = ["FraudEngine", "FraudSignal", "LocationSpoofingDetector", "CollusionRingDetector", "ImageFraudDetector"]
