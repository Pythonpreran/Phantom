def predict_next(ip, memory):
    risk = memory.risk(ip)

    if risk > 0.8:
        return {
            "next_attack": "LATERAL_MOVEMENT",
            "target": "/api/xyz/admin",
            "probability": 0.87,
            "eta": 10
        }

    if risk > 0.5:
        return {
            "next_attack": "SQL_INJECTION",
            "target": "/api/xyz/login",
            "probability": 0.72,
            "eta": 18
        }

    return {
        "next_attack": "RECON",
        "target": "/api/xyz/data",
        "probability": 0.45,
        "eta": 30
    }