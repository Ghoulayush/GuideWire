"""
LSTM Autoencoder for location sequence anomaly detection.

This implementation uses TensorFlow/Keras when available. It provides
training on synthetic GPS sequences and a `detect` method that returns
reconstruction error as an anomaly score.
"""
from __future__ import annotations

try:
    import numpy as np
    import tensorflow as tf
    TF_AVAILABLE = True
except Exception:
    np = None
    tf = None
    TF_AVAILABLE = False

import os
from typing import List


class LocationAutoencoder:
    def __init__(self, model_path: str = "models/location_autoencoder.h5", seq_len: int = 24, n_features: int = 2, latent_dim: int = 32):
        self.model_path = model_path
        self.seq_len = seq_len
        self.n_features = n_features
        self.latent_dim = latent_dim
        self.model = None
        if TF_AVAILABLE and os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
            except Exception:
                self.model = None

    def build_model(self):
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for LSTM autoencoder")

        inputs = tf.keras.Input(shape=(self.seq_len, self.n_features))
        x = tf.keras.layers.LSTM(64, return_sequences=True)(inputs)
        x = tf.keras.layers.LSTM(32)(x)
        latent = tf.keras.layers.Dense(self.latent_dim, activation="relu")(x)
        x = tf.keras.layers.RepeatVector(self.seq_len)(latent)
        x = tf.keras.layers.LSTM(32, return_sequences=True)(x)
        x = tf.keras.layers.LSTM(64, return_sequences=True)(x)
        outputs = tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(self.n_features))(x)

        model = tf.keras.Model(inputs, outputs)
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3), loss="mse")
        return model

    def train(self, sequences: List[List[List[float]]], epochs: int = 10, batch_size: int = 64, save: bool = True):
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for training the autoencoder")

        X = np.array(sequences, dtype=np.float32)
        model = self.build_model()
        model.fit(X, X, epochs=epochs, batch_size=batch_size, verbose=1)
        self.model = model
        if save:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model.save(self.model_path)

    def detect(self, sequence: List[List[float]]) -> float:
        """Return reconstruction MSE scaled 0-100 as anomaly score."""
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for detection")
        if self.model is None:
            raise RuntimeError("Model not loaded or trained")

        import numpy as _np
        X = _np.array([sequence], dtype=_np.float32)
        recon = self.model.predict(X)
        mse = float(_np.mean((_np.square(recon - X))))
        # scale to 0-100 based on heuristic
        score = min(100.0, mse * 1000.0)
        return score
