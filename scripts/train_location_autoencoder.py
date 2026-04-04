"""
Train the LSTM autoencoder on synthetic GPS sequences.

Usage:
    python scripts/train_location_autoencoder.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.fraud.location_autoencoder import LocationAutoencoder
import numpy as np


def generate_random_walk(n_sequences=2000, seq_len=24, base_lat=19.0, base_lon=72.8):
    seqs = []
    for _ in range(n_sequences):
        lat = base_lat + np.random.normal(0, 0.01)
        lon = base_lon + np.random.normal(0, 0.01)
        seq = []
        for t in range(seq_len):
            lat += np.random.normal(0, 0.002)
            lon += np.random.normal(0, 0.002)
            seq.append([lat, lon])
        seqs.append(seq)
    return seqs


def main():
    print("Generating synthetic GPS random walk sequences...")
    sequences = generate_random_walk(n_sequences=3000, seq_len=24)

    print(f"Training autoencoder on {len(sequences)} sequences...")
    ae = LocationAutoencoder()
    ae.train(sequences, epochs=5, batch_size=64)
    print("Saved model to models/location_autoencoder.h5")


if __name__ == "__main__":
    main()
