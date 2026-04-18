from collections import defaultdict, deque
from datetime import datetime

class AttackerMemory:
    def __init__(self):
        self.store = defaultdict(lambda: {
            "hits": 0,
            "normals": 0,
            "endpoints": defaultdict(int),
            "timeline": deque(maxlen=30)
        })

    def update(self, ip, event, result):
        s = self.store[ip]

        if result["prediction"] == "attack":
            s["hits"] += 1
        else:
            s["normals"] += 1

        ep = event.get("endpoint", "unknown")
        s["endpoints"][ep] += 1
        s["timeline"].append(datetime.utcnow().timestamp())

    def risk(self, ip):
        s = self.store[ip]
        total = s["hits"] + s["normals"]

        if total == 0:
            return 0.0

        attack_ratio = s["hits"] / total
        activity = len(s["timeline"]) / 30

        return round(min(1.0, attack_ratio * 0.75 + activity * 0.25), 3)


memory = AttackerMemory()