"""
PHANTOM — Validation Lab Routes
Simulates attacks to test PHANTOM's detection and response.
"""

import asyncio
import json
import random
import time
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db, ValidationTest, RequestLog, BlockedIP, Alert
from ..auth import require_role
from ..ml_engine import ml_engine
from ..realtime import manager

router = APIRouter(prefix="/api/validation", tags=["validation"])


class StartTestRequest(BaseModel):
    test_type: str  # brute_force, sql_injection, ddos


def _run_brute_force_test(db: Session, test_id: int):
    """Simulate a brute force attack."""
    test = db.query(ValidationTest).filter(ValidationTest.id == test_id).first()
    if not test:
        return

    results = []
    detected = 0
    blocked = 0
    total = 20
    detection_times = []

    for i in range(total):
        start = time.time()

        event = ml_engine.generate_event(attack_probability=0.85)
        event["attack_cat"] = "Brute Force"
        event["label"] = 1

        result = ml_engine.predict_event(event)
        dt = (time.time() - start) * 1000

        detection_times.append(dt)

        if result["prediction"] in ("attack", "suspicious"):
            detected += 1
        if result["prediction"] == "attack" and result["confidence"] > 0.8:
            blocked += 1

        results.append({
            "attempt": i + 1,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "detection_time_ms": round(dt, 2),
            "action": "blocked" if result["prediction"] == "attack" else "allowed"
        })

    test.status = "completed"
    test.completed_at = datetime.utcnow()
    test.total_requests = total
    test.detected_count = detected
    test.blocked_count = blocked
    test.avg_detection_time_ms = sum(detection_times) / len(detection_times)
    test.results_json = json.dumps(results)
    db.commit()


def _run_sql_injection_test(db: Session, test_id: int):
    """Simulate SQL injection attempts."""
    test = db.query(ValidationTest).filter(ValidationTest.id == test_id).first()
    if not test:
        return

    results = []
    detected = 0
    blocked = 0
    total = 15
    detection_times = []

    payloads = [
        "' OR 1=1 --", "'; DROP TABLE users; --", "' UNION SELECT * FROM passwords --",
        "1; SELECT * FROM information_schema.tables", "admin'--",
        "' OR 'x'='x", "1 AND 1=1", "' HAVING 1=1 --",
        "'; EXEC xp_cmdshell('dir'); --", "1 UNION ALL SELECT NULL,NULL,NULL --",
        "' OR EXISTS(SELECT * FROM users WHERE username='admin') --",
        "1; WAITFOR DELAY '0:0:5' --", "' AND SUBSTRING(@@version,1,1)='M' --",
        "admin' AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables))--",
        "' OR BENCHMARK(10000000,SHA1('test'))--"
    ]

    for i in range(total):
        start = time.time()

        event = ml_engine.generate_event(attack_probability=0.9)
        event["attack_cat"] = "Exploits"
        event["label"] = 1

        result = ml_engine.predict_event(event)
        dt = (time.time() - start) * 1000
        detection_times.append(dt)

        if result["prediction"] in ("attack", "suspicious"):
            detected += 1
        if result["prediction"] == "attack":
            blocked += 1

        results.append({
            "attempt": i + 1,
            "payload": payloads[i],
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "detection_time_ms": round(dt, 2),
            "action": "blocked" if result["prediction"] == "attack" else "monitored"
        })

    test.status = "completed"
    test.completed_at = datetime.utcnow()
    test.total_requests = total
    test.detected_count = detected
    test.blocked_count = blocked
    test.avg_detection_time_ms = sum(detection_times) / len(detection_times)
    test.results_json = json.dumps(results)
    db.commit()


def _run_ddos_test(db: Session, test_id: int):
    """Simulate DDoS attack."""
    test = db.query(ValidationTest).filter(ValidationTest.id == test_id).first()
    if not test:
        return

    results = []
    detected = 0
    blocked = 0
    total = 30
    detection_times = []

    for i in range(total):
        start = time.time()

        event = ml_engine.generate_event(attack_probability=0.8)
        event["attack_cat"] = "DoS"
        event["label"] = 1

        result = ml_engine.predict_event(event)
        dt = (time.time() - start) * 1000
        detection_times.append(dt)

        if result["prediction"] in ("attack", "suspicious"):
            detected += 1
        if result["prediction"] == "attack" and result["confidence"] > 0.75:
            blocked += 1

        results.append({
            "attempt": i + 1,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "detection_time_ms": round(dt, 2),
            "action": "blocked" if result["confidence"] > 0.75 else "monitored"
        })

    test.status = "completed"
    test.completed_at = datetime.utcnow()
    test.total_requests = total
    test.detected_count = detected
    test.blocked_count = blocked
    test.avg_detection_time_ms = sum(detection_times) / len(detection_times)
    test.results_json = json.dumps(results)
    db.commit()


@router.post("/start")
def start_test(
    req: StartTestRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Start a validation test."""
    test = ValidationTest(
        test_type=req.test_type,
        status="running",
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    runners = {
        "brute_force": _run_brute_force_test,
        "sql_injection": _run_sql_injection_test,
        "ddos": _run_ddos_test,
    }

    runner = runners.get(req.test_type)
    if runner:
        background_tasks.add_task(runner, db, test.id)

    return {"test_id": test.id, "status": "running", "test_type": req.test_type}


@router.get("/results/{test_id}")
def get_results(
    test_id: int,
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Get validation test results."""
    test = db.query(ValidationTest).filter(ValidationTest.id == test_id).first()
    if not test:
        return {"error": "Test not found"}

    results = json.loads(test.results_json) if test.results_json else []

    return {
        "id": test.id,
        "test_type": test.test_type,
        "status": test.status,
        "started_at": test.started_at.isoformat() if test.started_at else None,
        "completed_at": test.completed_at.isoformat() if test.completed_at else None,
        "total_requests": test.total_requests,
        "detected_count": test.detected_count,
        "blocked_count": test.blocked_count,
        "avg_detection_time_ms": round(test.avg_detection_time_ms, 2),
        "detection_rate": round(test.detected_count / max(test.total_requests, 1) * 100, 1),
        "results": results,
    }


@router.get("/history")
def get_history(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Get all validation test history."""
    tests = db.query(ValidationTest).order_by(ValidationTest.started_at.desc()).limit(20).all()

    return {
        "tests": [
            {
                "id": t.id,
                "test_type": t.test_type,
                "status": t.status,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "total_requests": t.total_requests,
                "detected_count": t.detected_count,
                "blocked_count": t.blocked_count,
                "detection_rate": round(t.detected_count / max(t.total_requests, 1) * 100, 1) if t.total_requests else 0,
                "avg_detection_time_ms": round(t.avg_detection_time_ms, 2),
            }
            for t in tests
        ]
    }
