def decide_action(risk):
    if risk > 0.85:
        return {"action": "DECEIVE", "intensity": 0.9}

    if risk > 0.6:
        return {"action": "DELAY", "intensity": 0.6}

    if risk > 0.3:
        return {"action": "HONEYPOT", "intensity": 0.4}

    return {"action": "MONITOR", "intensity": 0.1}