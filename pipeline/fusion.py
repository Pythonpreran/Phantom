"""
PHANTOM Module 3  --  Contrastive Fusion Engine
==============================================
Cross-layer threat confirmation using cosine similarity of latent vectors.

Enhancements:
- Identity-based tracking (user_id + session, not just IP)
- Multi-network zone awareness
"""

import time
from collections import defaultdict, deque
import torch
import torch.nn.functional as F


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two latent vectors."""
    v1 = torch.tensor(vec_a, dtype=torch.float32)
    v2 = torch.tensor(vec_b, dtype=torch.float32)

    # Avoid zero-division
    if v1.norm() < 1e-8 or v2.norm() < 1e-8:
        return 0.0

    sim = F.cosine_similarity(v1.unsqueeze(0), v2.unsqueeze(0))
    return sim.item()


class ContrastiveFusionEngine:
    """
    Collects alerts from multiple guards within a sliding time window.
    Confirms incidents only when multiple layers agree (cosine similarity ≥ threshold).

    Identity-aware: tracks by composite key = IP + user_id (not just IP).
    Multi-network: adds zone context to fusion decisions.
    """

    def __init__(self, window_seconds: int = 60, similarity_threshold: float = 0.6):
        self.window_seconds = window_seconds
        self.similarity_threshold = similarity_threshold

        # identity_key → deque of (timestamp, layer, latent_vec, anomaly_score, event)
        self.alert_window: dict = defaultdict(deque)

        # Stats
        self.total_alerts_ingested = 0
        self.total_confirmed = 0
        self.total_suppressed = 0

    def _identity_key(self, event: dict) -> str:
        """
        Build composite identity key: IP + user_id.
        Identity-based tracking: not just IP.
        """
        ip = event.get("source_ip", "unknown")
        identity = event.get("identity", {})
        user_id = identity.get("user_id", "unknown")
        return f"{ip}::{user_id}"

    def ingest_alert(
        self, event: dict, layer: str, latent_vec: list, anomaly_score: float
    ) -> dict:
        """
        Called whenever a guard flags an event.
        Returns fusion decision:
        {decision, severity, confirmed, similarity, layers, identity_key, zone_info}
        """
        self.total_alerts_ingested += 1
        now = time.time()
        identity_key = self._identity_key(event)
        zone_info = event.get("network_zone", {})

        self._purge_old(identity_key, now)
        self.alert_window[identity_key].append(
            (now, layer, latent_vec, anomaly_score, event)
        )

        layers_present = set(entry[1] for entry in self.alert_window[identity_key])

        if len(layers_present) >= 2:
            result = self._evaluate_fusion(identity_key, layers_present, zone_info)
        else:
            result = {
                "decision": "SINGLE_GUARD",
                "severity": "LOW",
                "confirmed": False,
                "similarity": 0.0,
                "layers": list(layers_present),
                "identity_key": identity_key,
                "zone_info": zone_info,
                "suppressed": True,
            }
            self.total_suppressed += 1

        result["source_ip"] = event.get("source_ip", "unknown")
        result["identity"] = event.get("identity", {})
        return result

    def _purge_old(self, key: str, now: float):
        """Remove events older than the correlation window."""
        while self.alert_window[key] and (
            now - self.alert_window[key][0][0]
        ) > self.window_seconds:
            self.alert_window[key].popleft()

    def _evaluate_fusion(
        self, identity_key: str, layers_present: set, zone_info: dict
    ) -> dict:
        """Compute max cosine similarity across all guard pairs."""
        entries = list(self.alert_window[identity_key])

        # Get most recent latent vec per layer
        by_layer = {}
        for ts, layer, lvec, score, evt in reversed(entries):
            if layer not in by_layer:
                by_layer[layer] = (lvec, score)

        vecs = list(by_layer.values())
        max_similarity = 0.0

        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                sim = cosine_similarity(vecs[i][0], vecs[j][0])
                max_similarity = max(max_similarity, sim)

        num_guards = len(layers_present)

        # Multi-network awareness: untrusted zones get severity boost
        zone_boost = 0
        trust = zone_info.get("trust", "high")
        if trust in ("untrusted", "low"):
            zone_boost = 1  # Elevate severity for untrusted zones

        if max_similarity >= self.similarity_threshold:
            self.total_confirmed += 1
            if num_guards == 3:
                severity = "CRITICAL"
            elif zone_boost > 0:
                severity = "CRITICAL"  # 2 guards + untrusted zone = critical
            else:
                severity = "HIGH"

            return {
                "decision": "CONFIRMED_INCIDENT",
                "severity": severity,
                "confirmed": True,
                "similarity": max_similarity,
                "layers": list(layers_present),
                "identity_key": identity_key,
                "zone_info": zone_info,
                "suppressed": False,
            }
        else:
            return {
                "decision": "WEAK_CORRELATION",
                "severity": "MEDIUM" if zone_boost == 0 else "HIGH",
                "confirmed": False,
                "similarity": max_similarity,
                "layers": list(layers_present),
                "identity_key": identity_key,
                "zone_info": zone_info,
                "suppressed": False,
            }

    def get_stats(self) -> dict:
        return {
            "total_alerts_ingested": self.total_alerts_ingested,
            "total_confirmed": self.total_confirmed,
            "total_suppressed": self.total_suppressed,
            "active_identities": len(self.alert_window),
        }
