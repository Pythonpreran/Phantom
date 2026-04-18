"""
PHANTOM CDL — Orchestration Engine (engine.py)
Wires together: AttackerMemory → NextMovePredictor → CountermeasureSelector.

Usage:
    from server.cdl import cdl_engine

    cdl_data = cdl_engine.process(ip, event, ml_result)
    # → { "risk": 0.82, "prediction": {...}, "action": {...}, "context": "..." }
"""

from .core import memory
from .predictor import predict_next
from .countermeasures import decide_action


class CDLEngine:
    """
    Cyber Defense Logic Engine.
    For every incoming event:
      1. Update attacker memory for the IP
      2. Compute risk score
      3. Predict next move
      4. Select automated countermeasure
    """

    def process(self, ip: str, event: dict, result: dict) -> dict:
        """
        Args:
            ip:     Simulated attacker IP
            event:  Raw event dict (may contain endpoint, attack_type, etc.)
            result: ML engine output { prediction, confidence, severity, ... }

        Returns:
            dict with risk, prediction, action, context
        """
        memory.update(ip, event, result)

        risk       = memory.risk(ip)
        prediction = predict_next(ip, memory)
        action     = decide_action(risk)
        context    = memory.get_context(ip)

        return {
            "risk_score":  risk,
            "prediction":  prediction,
            "action":      action,
            "context":     context,
        }


# Singleton — imported by both website.py and admin.py
cdl_engine = CDLEngine()
