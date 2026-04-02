"""
Image fraud detector (heuristic-first). Uses Pillow + imagehash when available.

Provides recycled-image detection (perceptual hash) and simple heuristics
for AI-generated / photoshopped images. For production, replace heuristics
with a trained CNN model.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
import os

try:
    from PIL import Image, ExifTags
    import imagehash
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


@dataclass
class ImageFraudResult:
    fake_probability: float
    authenticity_score: float
    recycled: bool
    details: Dict[str, Any]


class ImageFraudDetector:
    def __init__(self, known_hashes: List[str] | None = None, hash_size: int = 16):
        self.known_hashes = known_hashes or []
        self.hash_size = hash_size

    def _compute_phash(self, path: str):
        if not PIL_AVAILABLE:
            return None
        try:
            img = Image.open(path)
            h = imagehash.phash(img, hash_size=self.hash_size)
            return h
        except Exception:
            return None

    def detect_recycled(self, path: str, threshold: int = 6) -> Dict[str, Any]:
        """Return whether image is similar to known images by phash hamming distance."""
        ph = self._compute_phash(path)
        if ph is None:
            return {"recycled": False, "closest_distance": None}

        best = None
        for kh in self.known_hashes:
            try:
                other = imagehash.hex_to_hash(kh)
                dist = ph - other
                if best is None or dist < best:
                    best = dist
            except Exception:
                continue

        return {"recycled": (best is not None and best <= threshold), "closest_distance": best}

    def analyze(self, path: str) -> ImageFraudResult:
        """Simple analysis: recycled detection + heuristic checks."""
        details = {"path": path}
        recycled = False
        closest = None
        if PIL_AVAILABLE:
            ph = self._compute_phash(path)
            details['phash'] = str(ph) if ph is not None else None
            rec = self.detect_recycled(path)
            recycled = rec.get('recycled', False)
            closest = rec.get('closest_distance')

            # heuristics: missing exif may indicate generated image
            try:
                img = Image.open(path)
                exif = img._getexif() if hasattr(img, '_getexif') else None
                details['has_exif'] = bool(exif)
                details['size'] = img.size
            except Exception:
                details['has_exif'] = False
                details['size'] = None

        # score composition
        score = 0.0
        if recycled:
            score += 40.0
        if not details.get('has_exif', True):
            score += 20.0
        size = details.get('size')
        if size and (size[0] < 128 or size[1] < 128):
            score += 20.0

        fake_prob = min(1.0, score / 100.0)

        return ImageFraudResult(fake_probability=fake_prob, authenticity_score=(1 - fake_prob), recycled=recycled, details={**details, 'closest_distance': closest})
