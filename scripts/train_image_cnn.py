"""
Train a tiny image CNN with synthetic data for demo purposes.

Generates simple 'real' vs 'fake' images and trains a MobileNetV2 head.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.fraud.image_cnn import ImageCNNDetector
import numpy as np
import tensorflow as tf


def generate_images(n_per_class=200, img_size=(128, 128)):
    X = []
    y = []
    for i in range(n_per_class):
        # real-like images: smooth gradients
        base = np.linspace(0, 255, img_size[0] * img_size[1], dtype=np.uint8).reshape(img_size)
        img = np.stack([base, np.roll(base, i + 1, axis=0), np.roll(base, i + 2, axis=1)], axis=-1)
        img = img.astype('float32') / 255.0
        X.append(img)
        y.append(0)

    for i in range(n_per_class):
        # fake-like images: high-frequency noise
        img = np.random.rand(img_size[0], img_size[1], 3).astype('float32')
        X.append(img)
        y.append(1)

    X = np.array(X)
    y = np.array(y)
    # shuffle
    idx = np.random.permutation(len(X))
    return X[idx], y[idx]


def main():
    print("Generating synthetic image dataset...")
    X, y = generate_images(150, img_size=(128, 128))
    # train/val split
    split = int(0.8 * len(X))
    X_train, y_train = X[:split], y[:split]
    X_val, y_val = X[split:], y[split:]

    train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train)).batch(16).prefetch(1)
    val_ds = tf.data.Dataset.from_tensor_slices((X_val, y_val)).batch(16).prefetch(1)

    det = ImageCNNDetector()
    det.train(train_ds, val_ds, epochs=3)
    print("Saved image CNN to models/image_cnn.h5")


if __name__ == "__main__":
    main()
