"""
PHANTOM — Log Routes
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database import get_db, RequestLog
from ..auth import get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    prediction: Optional[str] = None,
    ip: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated logs with optional filters."""
    query = db.query(RequestLog).order_by(desc(RequestLog.timestamp))

    if prediction:
        query = query.filter(RequestLog.prediction == prediction)
    if ip:
        query = query.filter(RequestLog.ip_address.contains(ip))

    total = query.count()
    logs = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "logs": [
            {
                "id": log.id,
                "ip_address": log.ip_address,
                "endpoint": log.endpoint,
                "method": log.method,
                "status_code": log.status_code,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "response_time_ms": log.response_time_ms,
                "prediction": log.prediction,
                "confidence": log.confidence,
                "attack_type": log.attack_type,
            }
            for log in logs
        ]
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get aggregated log statistics."""
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    total = db.query(func.count(RequestLog.id)).scalar() or 0
    attacks = db.query(func.count(RequestLog.id)).filter(
        RequestLog.prediction == "attack"
    ).scalar() or 0
    suspicious = db.query(func.count(RequestLog.id)).filter(
        RequestLog.prediction == "suspicious"
    ).scalar() or 0

    last_hour = db.query(func.count(RequestLog.id)).filter(
        RequestLog.timestamp >= hour_ago
    ).scalar() or 0

    # Attack type distribution
    type_counts = db.query(
        RequestLog.attack_type, func.count(RequestLog.id)
    ).filter(
        RequestLog.attack_type.isnot(None)
    ).group_by(RequestLog.attack_type).all()

    return {
        "total_requests": total,
        "total_attacks": attacks,
        "total_suspicious": suspicious,
        "total_normal": total - attacks - suspicious,
        "last_hour": last_hour,
        "attack_types": {t: c for t, c in type_counts if t},
    }
