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
from .base_detector import FraudResult, FraudAction
try:
    from .nlp_detector import nlp_detector
except Exception:
    nlp_detector = None

try:
    from .predictive_scorer import predictive_scorer
except Exception:
    predictive_scorer = None

# Layer 6: Temporal detector (LSTM + heuristics)
try:
    from .temporal_detector import temporal_detector
except Exception:
    temporal_detector = None

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
        self.nlp_detector = nlp_detector
        self.location_isolation: Optional[object] = None

        if LocationIsolationDetector is not None:
            try:
                self.location_isolation = LocationIsolationDetector(model_path=f"{model_dir}/location_isolation.pkl")
            except Exception:
                self.location_isolation = None

        # Optional TF-based detectors: only keep instances if model loaded successfully
        self.location_autoenc = None
        if LocationAutoencoder is not None:
            try:
                _la = LocationAutoencoder(model_path=f"{model_dir}/location_autoencoder.h5")
                if getattr(_la, 'model', None) is not None:
                    self.location_autoenc = _la
            except Exception:
                self.location_autoenc = None

        self.image_cnn = None
        if ImageCNNDetector is not None:
            try:
                _cnn = ImageCNNDetector(model_path=f"{model_dir}/image_cnn.h5")
                if getattr(_cnn, 'model', None) is not None:
                    self.image_cnn = _cnn
            except Exception:
                self.image_cnn = None

        # Ensemble: allow fallback rule if model not available
        self.ensemble = None
        if FraudEnsemble is not None:
            try:
                _fe = FraudEnsemble(model_path=f"{model_dir}/fraud_ensemble.pkl")
                # keep the ensemble instance even if not trained — predict_proba implements a fallback rule
                self.ensemble = _fe
            except Exception:
                self.ensemble = None

        # Predictive scorer (Layer 5)
        self.predictive_scorer = predictive_scorer
        # Temporal detector (Layer 6)
        self.temporal_detector = temporal_detector

    def evaluate_claim(self, claim_data):
        """
        Evaluate claim using ALL 5 fraud detectors (Layers 1-5)
        Layer 5 (Predictive Scorer) combines everything into final score
        Accepts either a dict (`claim_data`) or a `Claim` object.
        """
        # Normalize to dict if a Claim object is passed
        if not isinstance(claim_data, dict):
            # try to build a simple dict from the Claim object
            try:
                claim_data = claim_data.__dict__
            except Exception:
                claim_data = {}

        detector_results: List[FraudResult] = []

        # Layer 1: Location spoofing
        if 'gps_history' in claim_data or 'trajectory' in claim_data:
            gps_data = claim_data.get('gps_history') or claim_data.get('trajectory')
            if gps_data:
                try:
                    loc_result = self.location_detector.detect(gps_data)
                    detector_results.append(loc_result)
                except Exception:
                    pass

        # Layer 2: Collusion detection
        if 'claims_in_area' in claim_data:
            try:
                col_result = self.collusion_detector.detect_rings(claim_data['claims_in_area'])
                detector_results.append(col_result)
            except Exception:
                pass

        # Layer 3: Image fraud detection
        if 'image_path' in claim_data or 'images' in claim_data:
            img_path = claim_data.get('image_path')
            images = claim_data.get('images') or ([img_path] if img_path else [])
            for img in images:
                try:
                    img_result = self.image_detector.detect(img)
                    detector_results.append(img_result)
                except Exception:
                    continue

        # Layer 4: NLP review fraud detection
        if 'review_text' in claim_data:
            try:
                nlp = getattr(self, 'nlp_detector', None)
                if nlp is not None:
                    nlp_result = nlp.detect(review_text=claim_data.get('review_text', ''), delivery_data=claim_data.get('delivery_data', {}))
                    detector_results.append(nlp_result)
            except Exception:
                pass

        # Layer 6: Temporal LSTM-based detector
        try:
            temporal = getattr(self, 'temporal_detector', None)
            if temporal is not None:
                # Prefer explicit claim history list for temporal detector
                claim_history = claim_data.get('claim_history')
                if not isinstance(claim_history, list):
                    # fall back if worker_history contains a list of claims
                    claim_history = claim_data.get('worker_history') if isinstance(claim_data.get('worker_history'), list) else claim_history
                if not isinstance(claim_history, list):
                    claim_history = []

                worker_id = claim_data.get('worker_id') or claim_data.get('worker') or claim_data.get('worker_ref') or 'unknown'
                try:
                    temp_result = temporal.detect(worker_id, claim_history)
                    detector_results.append(temp_result)
                except Exception:
                    pass
        except Exception:
            pass

        # Layer 5: Predictive Scorer (combines all results)
        if detector_results:
            worker_history = claim_data.get('worker_history', {})
            scorer = getattr(self, 'predictive_scorer', None)
            if scorer is not None:
                try:
                    final_result = scorer.predict(detector_results, worker_history)

                    # Also compute our weighted score so advanced detectors (e.g. Temporal)
                    # influence the final decision even when a predictive scorer exists.
                    try:
                        weights = {
                            "LocationSpoofingDetector": 0.20,
                            "CollusionRingDetector": 0.25,
                            "ImageFraudDetector": 0.20,
                            "NLPFraudDetector": 0.15,
                            "TemporalFraudDetector": 0.20,
                        }
                        total_score = 0.0
                        total_weight = 0.0
                        for r in detector_results:
                            if isinstance(r, dict):
                                name = r.get('detector_name')
                                try:
                                    score = int(r.get('fraud_score', 0))
                                except Exception:
                                    score = 0
                            else:
                                name = getattr(r, 'detector_name', None)
                                try:
                                    score = int(getattr(r, 'fraud_score', 0))
                                except Exception:
                                    score = 0
                            w = weights.get(name, 0.15)
                            total_score += score * w
                            total_weight += w

                        weighted_score = int(total_score / total_weight) if total_weight > 0 else 0
                    except Exception:
                        weighted_score = 0

                    # If any detector explicitly returns REJECT, boost the weighted score
                    try:
                        any_reject = any(
                            (getattr(r, 'action').value == "REJECT") if (not isinstance(r, dict) and hasattr(r, 'action')) else (str(r.get('action', '')).upper() == "REJECT")
                            for r in detector_results
                        )
                    except Exception:
                        any_reject = False

                    if any_reject:
                        weighted_score = max(weighted_score, 60)

                    # Choose the stronger signal between the predictive scorer and our weighted rule
                    final_score = max(int(getattr(final_result, 'fraud_score', 0)), weighted_score)

                    # Map to action using final_score thresholds
                    if final_score >= 70:
                        action = FraudAction.REJECT
                    elif final_score >= 40:
                        action = FraudAction.REVIEW
                    else:
                        action = FraudAction.APPROVE

                    return {
                        "fraud_score": final_score,
                        "action": action.value,
                        "reasons": [r.reason for r in detector_results],
                        "detector_results": [r.model_dump() if hasattr(r, 'model_dump') else (r if isinstance(r, dict) else vars(r)) for r in detector_results],
                        "final_decision": final_result.reason,
                        "confidence": max(getattr(final_result, 'confidence', 50), 70 if final_score >= 40 else 90),
                        "legacy_signals": []
                    }
                except Exception:
                    # fallback to simple aggregation if scorer fails
                    pass

            # If scorer not available, fallback to weighted aggregation of detector scores
            try:
                weights = {
                    "LocationSpoofingDetector": 0.20,
                    "CollusionRingDetector": 0.25,
                    "ImageFraudDetector": 0.20,
                    "NLPFraudDetector": 0.15,
                    "TemporalFraudDetector": 0.20,
                }
                total_score = 0.0
                total_weight = 0.0
                for r in detector_results:
                    # detector_name may be an attribute or a dict key
                    if isinstance(r, dict):
                        name = r.get('detector_name')
                        try:
                            score = int(r.get('fraud_score', 0))
                        except Exception:
                            score = 0
                    else:
                        name = getattr(r, 'detector_name', None)
                        try:
                            score = int(getattr(r, 'fraud_score', 0))
                        except Exception:
                            score = 0

                    weight = weights.get(name, 0.15)
                    total_score += score * weight
                    total_weight += weight

                final_score = int(total_score / total_weight) if total_weight > 0 else 0
            except Exception:
                final_score = 0

            # If any detector explicitly returns REJECT, boost final score to at least review level
            try:
                any_reject = any(
                    (getattr(r, 'action').value == "REJECT") if (not isinstance(r, dict) and hasattr(r, 'action')) else (str(r.get('action', '')).upper() == "REJECT")
                    for r in detector_results
                )
            except Exception:
                any_reject = False

            if any_reject:
                final_score = max(final_score, 60)

            # Map to action
            if final_score >= 70:
                action = FraudAction.REJECT
            elif final_score >= 40:
                action = FraudAction.REVIEW
            else:
                action = FraudAction.APPROVE

            return {
                "fraud_score": final_score,
                "action": action.value,
                "reasons": [r.reason for r in detector_results],
                "detector_results": [r.model_dump() if hasattr(r, 'model_dump') else (r if isinstance(r, dict) else vars(r)) for r in detector_results],
                "final_decision": f"Aggregated score {final_score}",
                "confidence": 70 if final_score >= 40 else 90,
                "legacy_signals": []
            }

        return {
            "fraud_score": 0,
            "action": "APPROVE",
            "reasons": ["No fraud detectors applied"],
            "detector_results": [],
            "final_decision": "No fraud signals detected",
            "confidence": 100,
            "legacy_signals": []
        }


__all__ = ["FraudEngine", "FraudSignal", "LocationSpoofingDetector", "CollusionRingDetector", "ImageFraudDetector"]
