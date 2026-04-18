"""
PHANTOM CDL — Attacker Memory (core.py)
Tracks per-IP behaviour history: attack hits, normal requests,
endpoint access patterns, activity timeline.
Risk score = weighted blend of attack ratio + recent activity.
"""
from collections import defaultdict, deque
from datetime import datetime


class AttackerMemory:
    def __init__(self):
        self.store = defaultdict(lambda: {
            "hits": 0,
            "normals": 0,
            "endpoints": defaultdict(int),
            "timeline": deque(maxlen=30),
        })

    def update(self, ip: str, event: dict, result: dict):
        s = self.store[ip]

        if result.get("prediction") == "attack":
            s["hits"] += 1
        else:
            s["normals"] += 1

        ep = event.get("endpoint", event.get("attack_type", "unknown"))
        s["endpoints"][ep] += 1
        s["timeline"].append(datetime.utcnow().timestamp())

    def risk(self, ip: str) -> float:
        s = self.store[ip]
        total = s["hits"] + s["normals"]

        if total == 0:
            return 0.0

        attack_ratio = s["hits"] / total
        activity    = len(s["timeline"]) / 30          # 0–1 based on last 30 events

        return round(min(1.0, attack_ratio * 0.75 + activity * 0.25), 3)

    def get_context(self, ip: str) -> str:
        """Return a human-readable context string for the logs table."""
        s = self.store[ip]
        total = s["hits"] + s["normals"]
        if total == 0:
            return "Initial behaviour analysis..."
        if s["hits"] == 0:
            return f"Normal pattern — {total} benign requests observed"
        top_ep = max(s["endpoints"], key=s["endpoints"].get, default="?")
        return (
            f"{s['hits']}/{total} requests flagged as attacks; "
            f"primary target: {top_ep}"
        )


# Module-level singleton
memory = AttackerMemory()
