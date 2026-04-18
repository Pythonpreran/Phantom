"""
PHANTOM Module 1  --  Ingestor & Normalizer
==========================================
Async consumer that normalizes raw events using the pretrained scaler.
"""

import os
import pickle
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from data.generate_synthetic import flatten_event_to_vector


class Normalizer:
    """
    Loads pretrained MinMaxScaler and normalizes events to 32-dim vectors.
    """

    def __init__(self, scaler_path: str = None):
        if scaler_path is None:
            scaler_path = os.path.join(
                os.path.dirname(__file__), "..", "models", "scaler.pkl"
            )
        with open(scaler_path, "rb") as f:
            self.scaler: MinMaxScaler = pickle.load(f)
        print("[Normalizer] Pretrained scaler loaded.")

    def normalize(self, event: dict) -> dict:
        """
        Takes a raw event, flattens to 32-dim, scales with pretrained scaler.
        Returns the event with normalized_vector filled.
        """
        raw_vec = flatten_event_to_vector(event)
        padded = raw_vec[:32] + [0.0] * max(0, 32 - len(raw_vec))
        arr = np.array([padded], dtype=np.float32)

        # Clip to scaler range to avoid warnings
        arr = np.clip(arr, self.scaler.data_min_, self.scaler.data_max_)
        normalized = self.scaler.transform(arr)[0]

        event["normalized_vector"] = normalized.tolist()
        return event

    def normalize_batch(self, events: list) -> list:
        """Normalize multiple events at once (for efficiency)."""
        vecs = []
        for event in events:
            raw_vec = flatten_event_to_vector(event)
            padded = raw_vec[:32] + [0.0] * max(0, 32 - len(raw_vec))
            vecs.append(padded)

        arr = np.array(vecs, dtype=np.float32)
        arr = np.clip(arr, self.scaler.data_min_, self.scaler.data_max_)
        normalized = self.scaler.transform(arr)

        for i, event in enumerate(events):
            event["normalized_vector"] = normalized[i].tolist()
        return events
