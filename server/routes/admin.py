"""
PHANTOM — Admin Routes
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database import get_db, RequestLog, BlockedIP, HoneypotEvent, Alert, User
from ..auth import require_role
from ..middleware import blocked_ips
from ..realtime import manager
from ..cdl import cdl_engine

router = APIRouter(prefix="/api/admin", tags=["admin"])


class BlockIPRequest(BaseModel):
    ip_address: str
    reason: str = "Manually blocked by admin"


@router.get("/dashboard")
def admin_dashboard(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Global admin dashboard data — all from DB, no simulation."""
    total_logs = db.query(func.count(RequestLog.id)).scalar() or 0
    total_attacks = db.query(func.count(RequestLog.id)).filter(
        RequestLog.prediction == "attack"
    ).scalar() or 0
    total_blocked = db.query(func.count(BlockedIP.id)).filter(
        BlockedIP.is_active == True
    ).scalar() or 0
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    honeypot_events = db.query(func.count(HoneypotEvent.id)).scalar() or 0

    # Recent alerts
    recent_alerts = db.query(Alert).order_by(desc(Alert.timestamp)).limit(20).all()

    # Attack distribution
    attack_dist = db.query(
        RequestLog.attack_type, func.count(RequestLog.id)
    ).filter(
        RequestLog.prediction == "attack",
        RequestLog.attack_type.isnot(None)
    ).group_by(RequestLog.attack_type).all()

    return {
        "total_requests": total_logs,
        "total_attacks": total_attacks,
        "total_blocked_ips": total_blocked,
        "total_alerts": total_alerts,
        "total_users": total_users,
        "honeypot_events": honeypot_events,
        "attack_distribution": {t: c for t, c in attack_dist if t},
        "active_ws_connections": manager.get_active_count(),
        "recent_alerts": [
            {
                "id": a.id, "severity": a.severity, "title": a.title,
                "description": a.description, "ip_address": a.ip_address,
                "attack_type": a.attack_type, "action_taken": a.action_taken,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "is_read": a.is_read,
                # ── CDL: live behavioural intelligence per IP ────────────────
                "cdl": cdl_engine.process(
                    a.ip_address or "unknown",
                    {"endpoint": a.action_taken or "unknown", "attack_type": a.attack_type or "unknown"},
                    {"prediction": "attack", "confidence": a.id},  # treat all alerts as attacks
                ) if a.ip_address else None,
            }
            for a in recent_alerts
        ]
    }


@router.get("/live-stats")
def live_stats(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Real-time stats from DB — polled every few seconds by admin dashboard."""
    total = db.query(func.count(RequestLog.id)).scalar() or 0
    attacks = db.query(func.count(RequestLog.id)).filter(RequestLog.prediction == "attack").scalar() or 0
    blocked = db.query(func.count(BlockedIP.id)).filter(BlockedIP.is_active == True).scalar() or 0
    suspicious = db.query(func.count(RequestLog.id)).filter(RequestLog.prediction == "suspicious").scalar() or 0

    # Requests in last 60 seconds
    recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
    rpm = db.query(func.count(RequestLog.id)).filter(RequestLog.timestamp >= recent_cutoff).scalar() or 0

    return {
        "total_requests": total,
        "total_attacks": attacks,
        "total_blocked": blocked,
        "total_suspicious": suspicious,
        "active_users": manager.get_active_count(),
        "rpm": rpm,
    }


@router.get("/chart-data")
def chart_data(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Returns time-bucketed request counts for the live traffic chart.
    25 buckets × 5 seconds = 2-minute window.
    """
    now = datetime.utcnow()
    buckets = []

    for i in range(24, -1, -1):  # oldest to newest
        bucket_start = now - timedelta(seconds=(i + 1) * 5)
        bucket_end = now - timedelta(seconds=i * 5)

        normal = db.query(func.count(RequestLog.id)).filter(
            RequestLog.timestamp >= bucket_start,
            RequestLog.timestamp < bucket_end,
            RequestLog.prediction == "normal"
        ).scalar() or 0

        suspicious = db.query(func.count(RequestLog.id)).filter(
            RequestLog.timestamp >= bucket_start,
            RequestLog.timestamp < bucket_end,
            RequestLog.prediction == "suspicious"
        ).scalar() or 0

        attack = db.query(func.count(RequestLog.id)).filter(
            RequestLog.timestamp >= bucket_start,
            RequestLog.timestamp < bucket_end,
            RequestLog.prediction == "attack"
        ).scalar() or 0

        secs_ago = i * 5
        label = "Now" if i == 0 else (f"{secs_ago}s" if secs_ago <= 60 else f"{secs_ago//60}m{secs_ago%60:02d}s")

        buckets.append({"time": label, "Normal": normal, "Suspicious": suspicious, "Attack": attack})

    return {"buckets": buckets}


@router.post("/block-ip")
def block_ip(
    req: BlockIPRequest,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    existing = db.query(BlockedIP).filter(BlockedIP.ip_address == req.ip_address).first()

    if existing:
        existing.is_active = True
        existing.reason = req.reason
        existing.blocked_by = "admin"
    else:
        blocked = BlockedIP(
            ip_address=req.ip_address, reason=req.reason,
            attack_type="Manual", confidence=1.0,
            blocked_by="admin", flagged=False,
        )
        db.add(blocked)

    blocked_ips.add(req.ip_address)
    db.commit()
    return {"status": "blocked", "ip": req.ip_address}


@router.delete("/unblock-ip/{ip_address}")
def unblock_ip(
    ip_address: str,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    record = db.query(BlockedIP).filter(BlockedIP.ip_address == ip_address).first()
    if record:
        record.is_active = False
        db.commit()

    blocked_ips.discard(ip_address)
    return {"status": "unblocked", "ip": ip_address}


@router.get("/blocked-ips")
def get_blocked_ips(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    ips = db.query(BlockedIP).filter(BlockedIP.is_active == True).order_by(
        desc(BlockedIP.blocked_at)
    ).all()

    return {
        "blocked_ips": [
            {
                "id": ip.id, "ip_address": ip.ip_address,
                "reason": ip.reason, "attack_type": ip.attack_type,
                "confidence": ip.confidence,
                "blocked_at": ip.blocked_at.isoformat() if ip.blocked_at else None,
                "blocked_by": ip.blocked_by,
                "flagged": getattr(ip, 'flagged', False),
            }
            for ip in ips
        ]
    }


@router.get("/honeypot")
def get_honeypot_events(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    events = db.query(HoneypotEvent).order_by(desc(HoneypotEvent.timestamp)).limit(100).all()
    return {
        "events": [
            {
                "id": e.id, "ip_address": e.ip_address, "endpoint": e.endpoint,
                "method": e.method, "payload": e.payload,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "event_type": e.event_type, "captured_data": e.captured_data,
            }
            for e in events
        ]
    }


@router.get("/predictions")
def get_predictions(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    predictions = db.query(
        RequestLog.prediction, func.count(RequestLog.id), func.avg(RequestLog.confidence)
    ).group_by(RequestLog.prediction).all()

    return {
        "predictions": {
            p: {"count": c, "avg_confidence": round(float(a or 0), 4)}
            for p, c, a in predictions if p
        }
    }


@router.get("/users")
def get_all_users(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """All users across all companies with company label."""
    users = db.query(User).order_by(User.company_id, User.id).all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "company_id": u.company_id,
                "company_name": u.company_name,
                "simulated_ip": u.simulated_ip,
                "is_blocked": u.is_blocked,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }
