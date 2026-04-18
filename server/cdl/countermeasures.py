"""
PHANTOM CDL — Countermeasures (countermeasures.py)
Decides the automated defensive response based on risk score.

Actions (escalating intensity):
  MONITOR  — passive observation, no action
  HONEYPOT — redirect suspicious IPs to trap endpoints
  DELAY    — introduce artificial response latency
  DECEIVE  — serve fake / misleading data to the attacker
"""


def decide_action(risk: float) -> dict:
    if risk > 0.85:
        return {"action": "DECEIVE",  "intensity": 0.9,
                "description": "Serving deceptive responses to mislead attacker"}

    if risk > 0.6:
        return {"action": "DELAY",    "intensity": 0.6,
                "description": "Introducing artificial latency to slow attacker"}

    if risk > 0.3:
        return {"action": "HONEYPOT", "intensity": 0.4,
                "description": "Redirecting to honeypot trap to capture attacker TTPs"}

    return     {"action": "MONITOR",  "intensity": 0.1,
                "description": "Passive monitoring — no active countermeasure needed"}
