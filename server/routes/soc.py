"""
PHANTOM — SOC Routes
====================
New API endpoints for Kill Chain status, Model Metrics, and SOC Playbooks.
Mounted at /api/soc/*
"""

from fastapi import APIRouter, Depends
from ..auth import require_role, get_current_user
from ..ml_engine import ml_engine
from .. import soc_engine

router = APIRouter(prefix="/api/soc", tags=["soc"])


@router.get("/kill-chain")
def get_kill_chain(min_stage: int = 0):
    """
    Return all IPs currently tracked in the kill chain,
    optionally filtered by minimum stage (0=all, 1=recon+, etc.)
    """
    threats = soc_engine.get_kill_chain_status(min_stage=min_stage)
    stats = soc_engine.get_kill_chain_stats()
    return {
        "threats": threats,
        "stats": stats,
        "stage_labels": {
            0: "CLEAN",
            1: "RECON",
            2: "INITIAL_ACCESS",
            3: "EXECUTION",
            4: "LATERAL_MOVEMENT",
            5: "EXFILTRATION",
        },
    }


@router.get("/kill-chain/{ip}")
def get_kill_chain_ip(ip: str):
    """Return the kill chain state for a specific IP address."""
    state = soc_engine.get_kill_chain_for_ip(ip)
    if state is None:
        return {"found": False, "ip": ip, "message": "No kill chain record for this IP"}
    return {"found": True, **state}


@router.get("/model-metrics")
def get_model_metrics():
    """
    Return the LightGBM model performance metrics from model_config.json.
    Accuracy, Macro F1, ROC-AUC, FPR, FNR, feature counts, best hyperparams.
    """
    metrics = ml_engine.get_model_metrics()
    if not metrics:
        return {
            "error": "model_config.json not loaded",
            "model": "LightGBM (Optuna-tuned)",
        }
    return {
        "model": "LightGBM (Optuna-tuned)",
        "dataset": "UNSW-NB15",
        "train_samples": metrics.get("train_shape", [0])[0],
        "test_samples": metrics.get("test_shape", [0])[0],
        "accuracy": metrics.get("accuracy", 0),
        "macro_f1": metrics.get("macro_f1", 0),
        "roc_auc": metrics.get("roc_auc", 0),
        "fpr": metrics.get("fpr", 0),
        "fnr": metrics.get("fnr", 0),
        "threshold": metrics.get("threshold", 0.85),
        "features_before_selection": metrics.get("features_before_selection", 206),
        "features_after_selection": metrics.get("features_after_selection", 18),
        "best_params": metrics.get("best_params", {}),
    }


@router.get("/playbook/{attack_type}")
def get_playbook(attack_type: str, ip: str = "unknown", confidence: float = 0.9):
    """Return a structured SOC playbook for the given attack type."""
    return soc_engine.get_playbook(attack_type, ip, confidence)


@router.get("/feature-importance")
def get_feature_importance():
    """
    Return the global LightGBM feature importances (across all predictions).
    Uses the model's built-in feature_importances_.
    """
    top5 = ml_engine.explain_prediction(0.9)
    return {
        "method": "LightGBM feature_importances_ (gain)",
        "top_features": [
            {"feature": name, "importance": pct, "importance_pct": f"{pct * 100:.1f}%"}
            for name, pct in top5
        ],
    }
