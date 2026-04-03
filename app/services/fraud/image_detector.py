"""
Image Fraud Detector - Layer 3 of Fraud Detection System
Detects AI-generated and manipulated images using CNN + heuristic fallback
Author: Member 2 (adapted)
"""

import os
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, Optional

import numpy as np
from .base_detector import standardize_result


@dataclass
class ImageFraudResult:
    fake_probability: float
    authenticity_score: float
    recycled: bool
    details: Dict[str, Any]


class ImageFraudDetector:
    """
    Detects fake/AI-generated images submitted as claim evidence
    Uses pre-trained CNN if available, falls back to heuristics
    """

    def __init__(self, known_hashes: Optional[list] = None, model_path: str = "models/image_cnn.h5"):
        self.cnn_model = None
        self.model_loaded = False
        self.model_path = model_path
        # known_hashes allows passing previously seen phash hex strings
        self.known_hashes = set(known_hashes or [])
        self._seen_hashes = set()
        self._load_model()

    def _load_model(self):
        """Load pre-trained CNN model if available and working"""
        if not os.path.exists(self.model_path):
            print(f"ℹ️ No CNN model found at {self.model_path}. Using heuristic detection.")
            return

        try:
            # Try to import TensorFlow (optional dependency)
            try:
                from tensorflow.keras.models import load_model
            except Exception:
                print("ℹ️ TensorFlow not installed or not importable. Using heuristic detection.")
                return

            # Load the model
            self.cnn_model = load_model(self.model_path)
            self.model_loaded = True
            print("✅ CNN model loaded successfully for image fraud detection!")

        except Exception as e:
            print(f"⚠️ Could not load CNN model: {e}")
            print("   Falling back to heuristic detection.")
            self.cnn_model = None
            self.model_loaded = False

    def detect(self, image_path: str) -> Dict[str, Any]:
        """
        Detect if an image is fake, AI-generated, or manipulated

        Returns dict:
        {
            "fraud_score": int (0-100),
            "action": "APPROVE" | "REVIEW" | "REJECT",
            "reason": str,
            "confidence": int (0-100),
            "details": {...}
        }
        """

        # Check if file exists
        if not os.path.exists(image_path):
            raw = {
                "fraud_score": 0,
                "action": "APPROVE",
                "reason": "No image submitted for verification",
                "confidence": 100,
                "details": {"path": image_path},
            }
            return standardize_result(raw, "ImageFraudDetector")

        # Use CNN if available, otherwise fallback to heuristics
        if self.model_loaded and self.cnn_model is not None:
            raw = self._cnn_analyze(image_path)
        else:
            raw = self._heuristic_analyze(image_path)

        return standardize_result(raw, "ImageFraudDetector")

    def _cnn_analyze(self, image_path: str) -> Dict[str, Any]:
        """Use deep learning CNN for fraud detection"""
        try:
            from tensorflow.keras.preprocessing import image
            from tensorflow.keras.applications.resnet50 import preprocess_input

            # Load and preprocess image
            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Predict fraud probability
            prediction = float(self.cnn_model.predict(img_array, verbose=0)[0][0])
            fraud_score = int(prediction * 100)

            # Determine action
            if fraud_score >= 70:
                action = "REJECT"
                reason = f"AI-generated or heavily manipulated image detected ({fraud_score}% confidence)"
            elif fraud_score >= 40:
                action = "REVIEW"
                reason = f"Suspicious image patterns detected ({fraud_score}% confidence)"
            else:
                action = "APPROVE"
                reason = "Image appears authentic"

            return {
                "fraud_score": fraud_score,
                "action": action,
                "reason": reason,
                "confidence": fraud_score if fraud_score >= 40 else 100 - fraud_score,
                "details": {"path": image_path, "model_used": os.path.basename(self.model_path)},
            }

        except Exception as e:
            print(f"CNN analysis failed: {e}, falling back to heuristics")
            return self._heuristic_analyze(image_path)

    def _heuristic_analyze(self, image_path: str) -> Dict[str, Any]:
        """Fallback heuristic detection (always works, no dependencies)"""

        fraud_score = 0
        reasons = []

        # Get file info
        file_name = os.path.basename(image_path).lower()
        try:
            file_size = os.path.getsize(image_path)
        except Exception:
            file_size = 0

        # Heuristic 1: AI-generation keywords in filename
        ai_patterns = ['dalle', 'midjourney', 'stable', 'generated', 'ai', 'synthetic']
        if any(pattern in file_name for pattern in ai_patterns):
            fraud_score += 40
            reasons.append("Filename suggests AI generation")

        # Heuristic 2: Unusual file size
        if file_size > 0 and file_size < 10000:  # Less than 10KB
            fraud_score += 25
            reasons.append("File unusually small (possible AI compression)")
        elif file_size > 5000000:  # More than 5MB
            fraud_score += 15
            reasons.append("File unusually large (possible manipulation)")

        # Heuristic 3: Check for duplicate submissions (hash-based)
        file_hash = self._get_file_hash(image_path)
        if file_hash and self._is_duplicate_image(file_hash):
            fraud_score += 50
            reasons.append("Image previously submitted in different claim")

        # Store hash for future duplicate detection
        if file_hash:
            self._store_image_hash(file_hash)

        # Cap at 100
        fraud_score = min(fraud_score, 100)

        # Determine action
        if fraud_score >= 60:
            action = "REJECT"
        elif fraud_score >= 30:
            action = "REVIEW"
        else:
            action = "APPROVE"

        reason = " | ".join(reasons) if reasons else "No fraud indicators detected"

        return {
            "fraud_score": int(fraud_score),
            "action": action,
            "reason": reason,
            "confidence": 80 if fraud_score == 0 else 70,
            "details": {"path": image_path, "file_size": file_size, "hash": file_hash},
        }

    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for duplicate detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _is_duplicate_image(self, file_hash: str) -> bool:
        """Check if image hash was seen before"""
        return (file_hash in self._seen_hashes) or (file_hash in self.known_hashes)

    def _store_image_hash(self, file_hash: str):
        """Store image hash for future duplicate detection"""
        if file_hash:
            self._seen_hashes.add(file_hash)

    # Backwards-compatible method used elsewhere in codebase
    def analyze(self, image_path: str) -> ImageFraudResult:
        """Return `ImageFraudResult` dataclass for legacy callers."""
        d = self.detect(image_path)
        # Support both standardized FraudResult (pydantic) and legacy dict
        if hasattr(d, "model_dump"):
            d_dict = d.model_dump()
        elif isinstance(d, dict):
            d_dict = d
        else:
            # Try attribute access
            try:
                d_dict = {"fraud_score": getattr(d, "fraud_score", 0), "reason": getattr(d, "reason", ""), "details": getattr(d, "details", {})}
            except Exception:
                d_dict = {"fraud_score": 0, "reason": "", "details": {}}

        fake_prob = float(d_dict.get('fraud_score', 0)) / 100.0
        recycled = 'previously submitted' in d_dict.get('reason', '').lower() or (d_dict.get('details', {}) or {}).get('hash') in getattr(self, '_seen_hashes', set())
        details = d_dict.get('details', {})
        return ImageFraudResult(fake_probability=fake_prob, authenticity_score=1.0 - fake_prob, recycled=recycled, details=details)


# Singleton instance for app-wide use
image_detector = ImageFraudDetector()
