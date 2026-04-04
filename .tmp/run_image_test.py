#!/usr/bin/env python3
import tempfile
import os
import numpy as np
import sys

# Ensure workspace root is on sys.path so `app` package imports work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

from app.services.fraud.image_detector import ImageFraudDetector


def main():
    det = ImageFraudDetector()
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    p = f.name
    f.close()
    try:
        if PILImage is None:
            print('PIL not available; skipping image creation and analysis')
            return
        img = PILImage.new('RGB', (200, 200), (73, 109, 137))
        img.save(p)
        res = det.analyze(p)
        print('ANALYZE_RESULT:', res)
        try:
            from app.services.fraud.image_cnn import ImageCNNDetector
            cnn = ImageCNNDetector()
            print('CNN_MODEL_LOADED:', cnn.model is not None)
            if cnn.model is not None:
                arr = np.array(PILImage.open(p).convert('RGB')).astype('float32') / 255.0
                prob = cnn.predict_image(arr)
                print('CNN_PROB:', prob)
        except Exception as e:
            print('CNN_ERROR:', e)
    finally:
        try:
            os.unlink(p)
        except Exception:
            pass


if __name__ == '__main__':
    main()
