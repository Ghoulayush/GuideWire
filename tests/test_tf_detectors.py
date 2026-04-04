import os
import numpy as np
import pytest

from app.services.fraud import location_autoencoder as la_mod
from app.services.fraud import image_cnn as ic_mod


def test_location_autoencoder_detect():
    if not getattr(la_mod, "TF_AVAILABLE", False):
        pytest.skip("TensorFlow not available")

    la = la_mod.LocationAutoencoder()

    # If model not pre-saved, do a brief synthetic train to enable detect
    if la.model is None:
        seq_len = la.seq_len
        n_features = la.n_features
        rng = np.random.RandomState(42)
        # 100 small random-walk sequences
        X = np.cumsum(rng.normal(scale=0.01, size=(100, seq_len, n_features)), axis=1).astype(np.float32)
        la.train(X, epochs=2, batch_size=16, save=False)

    # build a normal sequence and a sequence with a large jump (anomaly)
    rng2 = np.random.RandomState(1)
    normal_seq = np.cumsum(rng2.normal(scale=0.01, size=(la.seq_len, la.n_features)), axis=0).astype(float).tolist()
    anomaly_seq = [list(x) for x in normal_seq]
    anomaly_seq[5] = [anomaly_seq[5][0] + 10.0, anomaly_seq[5][1] + 10.0]

    normal_score = la.detect(normal_seq)
    anomaly_score = la.detect(anomaly_seq)

    assert isinstance(normal_score, float)
    assert isinstance(anomaly_score, float)
    assert 0.0 <= normal_score <= 100.0
    assert 0.0 <= anomaly_score <= 100.0
    assert anomaly_score >= normal_score


def test_image_cnn_predict_image():
    if not getattr(ic_mod, "TF_AVAILABLE", False):
        pytest.skip("TensorFlow not available")

    det = ic_mod.ImageCNNDetector()
    # If model file not present or not loaded, skip — building MobileNet weights in-test is heavy
    if det.model is None:
        pytest.skip("Image CNN model not present; skipping heavy model build")

    img = np.random.RandomState(2).randint(0, 256, size=(det.input_shape[0], det.input_shape[1], det.input_shape[2])).astype(np.float32)
    pred = det.predict_image(img)

    assert isinstance(pred, float)
    assert 0.0 <= pred <= 1.0
