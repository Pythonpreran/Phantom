from .core import memory
from .predictor import predict_next
from .countermeasures import decide_action

class CDLEngine:
    def process(self, ip, event, result):
        memory.update(ip, event, result)

        risk = memory.risk(ip)
        prediction = predict_next(ip, memory)
        action = decide_action(risk)

        return {
            "risk": risk,
            "prediction": prediction,
            "action": action
        }


cdl_engine = CDLEngine()