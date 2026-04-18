"""
PHANTOM Module 2  --  Detector (Runtime)
=======================================
Loads pretrained autoencoders + thresholds at startup.
Performs inference on normalized events  --  NO training during demo.
"""

import os
import json
import torch
import numpy as np
from models.autoencoder import SpecialistAutoencoder


class AnomalyDetector:
    """
    Loads all 3 pretrained specialist autoencoders.
    Runs inference at startup speed  --  no training, no gradient computation.
    """

    def __init__(self, models_dir: str = None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "..", "models")

        self.models = {}
        self.thresholds = {}

        # Load thresholds
        thresholds_path = os.path.join(models_dir, "thresholds.json")
        with open(thresholds_path, "r") as f:
            self.thresholds = json.load(f)

        # Load pretrained models
        for layer in ["network", "application", "endpoint"]:
            model = SpecialistAutoencoder(input_dim=32)
            model_path = os.path.join(models_dir, f"ae_{layer}.pt")
            model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            model.eval()
            self.models[layer] = model
            print(f"[Detector] Guard {layer.upper()} loaded (theta={self.thresholds[layer]:.4f})")

        print("[Detector] All 3 pretrained guards online. No training needed.")

    def detect(self, event: dict) -> dict:
        """
        Run anomaly detection on a single normalized event.
        Returns detection result with anomaly_score, is_anomalous, latent_vector.
        """
        layer = event["layer"]
        vec = event.get("normalized_vector")

        if vec is None or layer not in self.models:
            return {
                "event_id": event.get("event_id"),
                "layer": layer,
                "recon_error": 0.0,
                "threshold": 0.0,
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "latent_vector": [0.0, 0.0, 0.0, 0.0],
            }

        model = self.models[layer]
        threshold = self.thresholds[layer]

        x = torch.tensor([vec], dtype=torch.float32)

        with torch.no_grad():
            recon_error = model.reconstruction_error(x).item()
            latent = model.get_latent(x).squeeze().tolist()

        anomaly_score = recon_error / threshold if threshold > 0 else 0.0
        is_anomalous = recon_error > threshold

        return {
            "event_id": event.get("event_id"),
            "layer": layer,
            "recon_error": recon_error,
            "threshold": threshold,
            "anomaly_score": anomaly_score,
            "is_anomalous": is_anomalous,
            "latent_vector": latent if isinstance(latent, list) else [latent],
        }

    def detect_batch(self, events: list) -> list:
        """Batch detection for efficiency."""
        results = []
        # Group by layer for batch processing
        by_layer = {}
        for event in events:
            layer = event["layer"]
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(event)

        for layer, layer_events in by_layer.items():
            if layer not in self.models:
                continue

            model = self.models[layer]
            threshold = self.thresholds[layer]

            vecs = [e["normalized_vector"] for e in layer_events if e.get("normalized_vector")]
            if not vecs:
                continue

            x = torch.tensor(vecs, dtype=torch.float32)

            with torch.no_grad():
                recon_errors = model.reconstruction_error(x).numpy()
                latents = model.get_latent(x).numpy()

            for i, event in enumerate(layer_events):
                if event.get("normalized_vector") is None:
                    continue
                error = float(recon_errors[i])
                latent = latents[i].tolist()
                score = error / threshold if threshold > 0 else 0.0

                results.append({
                    "event_id": event.get("event_id"),
                    "layer": layer,
                    "recon_error": error,
                    "threshold": threshold,
                    "anomaly_score": score,
                    "is_anomalous": error > threshold,
                    "latent_vector": latent,
                    "event": event,  # pass through for downstream
                })

        return results
