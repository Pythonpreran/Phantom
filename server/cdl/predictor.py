"""
PHANTOM CDL — Next-Move Predictor (predictor.py)
Uses the per-IP risk score from AttackerMemory to forecast the
attacker's most likely next action and its ETA.
"""


def predict_next(ip: str, memory) -> dict:
    risk = memory.risk(ip)

    if risk > 0.8:
        return {
            "next_attack": "LATERAL_MOVEMENT",
            "target": "/api/xyz/admin",
            "probability": 0.87,
            "eta_seconds": 10,
        }

    if risk > 0.5:
        return {
            "next_attack": "SQL_INJECTION",
            "target": "/api/xyz/login",
            "probability": 0.72,
            "eta_seconds": 18,
        }

    return {
        "next_attack": "RECON",
        "target": "/api/xyz/data",
        "probability": 0.45,
        "eta_seconds": 30,
    }
