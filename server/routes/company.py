"""
PHANTOM — Company Routes (data filtered by company_id)
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database import get_db, RequestLog, BlockedIP, Alert, User
from ..auth import require_role

router = APIRouter(prefix="/api/company", tags=["company"])


@router.get("/dashboard")
def company_dashboard(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Company-specific dashboard data — filtered by company_id."""
    cid = user.company_id
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)

    total = db.query(func.count(RequestLog.id)).filter(
        RequestLog.company_id == cid
    ).scalar() or 0
    attacks = db.query(func.count(RequestLog.id)).filter(
        RequestLog.company_id == cid, RequestLog.prediction == "attack"
    ).scalar() or 0
    suspicious = db.query(func.count(RequestLog.id)).filter(
        RequestLog.company_id == cid, RequestLog.prediction == "suspicious"
    ).scalar() or 0
    blocked = db.query(func.count(BlockedIP.id)).filter(
        BlockedIP.is_active == True, BlockedIP.company_id == cid
    ).scalar() or 0

    last_hour_requests = db.query(func.count(RequestLog.id)).filter(
        RequestLog.company_id == cid, RequestLog.timestamp >= hour_ago
    ).scalar() or 0

    total_users = db.query(func.count(User.id)).filter(
        User.company_id == cid
    ).scalar() or 0

    severity_dist = db.query(
        RequestLog.prediction, func.count(RequestLog.id)
    ).filter(RequestLog.company_id == cid).group_by(RequestLog.prediction).all()

    return {
        "total_requests": total,
        "total_attacks": attacks,
        "total_suspicious": suspicious,
        "blocked_ips": blocked,
        "total_users": total_users,
        "last_hour_requests": last_hour_requests,
        "system_status": "operational",
        "severity_distribution": {p: c for p, c in severity_dist if p},
        "company_name": user.company_name or user.company_id,
    }


@router.get("/users")
def get_company_users(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """List users belonging to this company."""
    cid = user.company_id
    users = db.query(User).filter(User.company_id == cid, User.role == "user").all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "simulated_ip": u.simulated_ip,
                "is_blocked": u.is_blocked,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.get("/logs")
def get_company_logs(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Recent request logs for this company."""
    cid = user.company_id
    logs = db.query(RequestLog).filter(
        RequestLog.company_id == cid
    ).order_by(desc(RequestLog.timestamp)).limit(100).all()
    return {
        "logs": [
            {
                "id": l.id,
                "ip_address": l.ip_address,
                "endpoint": l.endpoint,
                "method": l.method,
                "status_code": l.status_code,
                "prediction": l.prediction,
                "confidence": l.confidence,
                "attack_type": l.attack_type,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ]
    }


@router.get("/threats")
def get_threats(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Get detected threats for this company."""
    cid = user.company_id
    threats = db.query(RequestLog).filter(
        RequestLog.company_id == cid,
        RequestLog.prediction.in_(["attack", "suspicious"])
    ).order_by(desc(RequestLog.timestamp)).limit(100).all()

    return {
        "threats": [
            {
                "id": t.id,
                "ip_address": t.ip_address,
                "endpoint": t.endpoint,
                "method": t.method,
                "prediction": t.prediction,
                "confidence": t.confidence,
                "attack_type": t.attack_type,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "status_code": t.status_code,
            }
            for t in threats
        ]
    }


@router.get("/blocked")
def get_blocked(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Get blocked IPs for this company."""
    cid = user.company_id
    ips = db.query(BlockedIP).filter(
        BlockedIP.is_active == True, BlockedIP.company_id == cid
    ).order_by(desc(BlockedIP.blocked_at)).all()

    return {
        "blocked_ips": [
            {
                "id": ip.id,
                "ip_address": ip.ip_address,
                "reason": ip.reason,
                "attack_type": ip.attack_type,
                "confidence": ip.confidence,
                "blocked_at": ip.blocked_at.isoformat() if ip.blocked_at else None,
                "blocked_by": ip.blocked_by,
                "flagged": getattr(ip, 'flagged', False),
            }
            for ip in ips
        ]
    }


@router.get("/alerts")
def get_alerts(
    user=Depends(require_role("company", "admin")),
    db: Session = Depends(get_db)
):
    """Get recent alerts for this company."""
    cid = user.company_id
    alerts = db.query(Alert).filter(
        Alert.company_id == cid
    ).order_by(desc(Alert.timestamp)).limit(50).all()

    return {
        "alerts": [
            {
                "id": a.id,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "ip_address": a.ip_address,
                "attack_type": a.attack_type,
                "action_taken": a.action_taken,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in alerts
        ]
    }
