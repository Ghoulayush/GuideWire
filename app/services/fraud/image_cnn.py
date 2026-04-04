"""
CNN image classifier using transfer learning (MobileNetV2) to detect fake/real images.
Uses TensorFlow/Keras when available.
"""
from __future__ import annotations
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except Exception:
    tf = None
    TF_AVAILABLE = False

import os
from typing import Optional


class ImageCNNDetector:
    def __init__(self, model_path: str = "models/image_cnn.h5", input_shape=(128, 128, 3)):
        self.model_path = model_path
        self.input_shape = input_shape
        self.model = None
        if TF_AVAILABLE and os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
            except Exception:
                self.model = None

    def build_model(self):
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for ImageCNNDetector")

        base = tf.keras.applications.MobileNetV2(input_shape=self.input_shape, include_top=False, weights='imagenet')
        base.trainable = False
        inputs = tf.keras.Input(shape=self.input_shape)
        x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
        x = base(x, training=False)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.Dense(128, activation='relu')(x)
        outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
        model = tf.keras.Model(inputs, outputs)
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-4), loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def train(self, train_ds, val_ds, epochs: int = 5, save: bool = True):
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for training")
        model = self.build_model()
        model.fit(train_ds, validation_data=val_ds, epochs=epochs)
        self.model = model
        if save:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model.save(self.model_path)

    def predict_image(self, img):
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for prediction")
        if self.model is None:
            raise RuntimeError("Model not loaded or trained")
        import numpy as np
        arr = tf.image.resize(img, self.input_shape[:2])
        arr = tf.expand_dims(arr, 0)
        pred = float(self.model.predict(arr)[0][0])
        # pred is probability of class 1 (fake)
        return pred
