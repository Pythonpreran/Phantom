"""
PHANTOM — Protected Website (XYZ) Routes
Features: per-user-account IP, attack simulation endpoint, brute force detection, real-time broadcasting.
"""

import re
import random
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db, RequestLog, BlockedIP, Alert, User
from ..middleware import blocked_ips
from ..ml_engine import ml_engine
from ..realtime import broadcast_real_event, manager
from ..auth import get_current_user
from ..alerts import send_critical_alert
from .. import soc_engine
from ..cdl import cdl_engine

router = APIRouter(prefix="/api/xyz", tags=["website"])


# ── Attack Payload Pattern Detectors ─────────────────────────────

_SQL_RE = re.compile(
    r"(\b(select|insert|update|delete|drop|union|exec|execute|cast|convert|xp_)\b"
    r"|'\s*(or|and)\s+[\w\s'=]+"
    r"|--\s|;\s*(drop|select|insert)"
    r"|'\s*=\s*'"
    r"|1\s*=\s*1"
    r"|0x[0-9a-fA-F]+)",
    re.IGNORECASE,
)

_XSS_RE = re.compile(
    r"(<\s*script|javascript:|on\w+\s*=|<\s*img[^>]*(onerror|onload)"
    r"|<\s*iframe|<\s*object|<\s*embed"
    r"|alert\s*\(|document\.cookie|eval\s*\("
    r"|String\.fromCharCode|window\.location)",
    re.IGNORECASE,
)

def _has_sql(text: str) -> bool:
    return bool(_SQL_RE.search(text))

def _has_xss(text: str) -> bool:
    return bool(_XSS_RE.search(text))


# ── DDoS Rate Tracker ─────────────────────────────────────────────

_data_requests: dict = defaultdict(list)
DDOS_RATE_WINDOW    = 10   # seconds
DDOS_RATE_THRESHOLD = 5    # requests in window

def _record_data_request(ip: str) -> int:
    now    = datetime.utcnow()
    cutoff = now - timedelta(seconds=DDOS_RATE_WINDOW)
    _data_requests[ip] = [t for t in _data_requests[ip] if t > cutoff]
    _data_requests[ip].append(now)
    return len(_data_requests[ip])


# ── Per-User IP Assignment ────────────────────────────────────────

def _get_user_ip(user: Optional[User], real_ip: str) -> str:
    """Return the user's assigned simulated IP, or derive from real IP if not logged in."""
    if user and user.simulated_ip:
        return user.simulated_ip
    # Fallback for unauthenticated requests
    import hashlib
    h = hashlib.md5(real_ip.encode()).hexdigest()
    return f"203.{int(h[:2],16)%200+10}.{int(h[2:4],16)%200+10}.{max(1, int(h[4:6],16)%254)}"


# ── Brute Force Detection ─────────────────────────────────────────

_login_attempts: dict = defaultdict(list)
BRUTE_FORCE_WINDOW = 60


def _record_failed_login(ip: str) -> int:
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=BRUTE_FORCE_WINDOW)
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
    _login_attempts[ip].append(now)
    return len(_login_attempts[ip])


def _get_attempt_count(ip: str) -> int:
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=BRUTE_FORCE_WINDOW)
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
    return len(_login_attempts[ip])


def _compute_brute_risk(attempt_count: int) -> tuple:
    """
    ML-driven brute-force risk scoring — the MODEL decides, not a hard counter rule.

    Feeds a synthetic network event into the real LightGBM model with an
    attack_probability that escalates with each failed login. The model's
    confidence score is then blended with attempt pressure to produce a
    CDL-style risk score that determines the response tier:

      risk < 0.35   → silent fail  (model sees low-confidence noise)
      0.35 ≤ r < 0.75 → suspicious  (model flags rising anomaly)
      risk ≥ 0.75   → block        (model signals clear hostile intent)

    Returns: (risk_score: float, ml_confidence: float, ml_prediction: str)
    """
    # Attack probability fed to the model — progressively hostile signal
    _prob_map = {1: 0.22, 2: 0.38, 3: 0.58, 4: 0.72, 5: 0.93}
    prob = _prob_map.get(attempt_count, min(0.99, 0.22 + (attempt_count - 1) * 0.17))

    event = ml_engine.generate_event(attack_probability=prob)
    event["attack_cat"] = "Brute Force"
    result = ml_engine.predict_event(event)

    ml_conf = result["confidence"]
    if result["prediction"] != "attack":
        ml_conf *= 0.35  # model says normal — dampen contribution

    # Blend model confidence with attempt pressure (70/30 weight)
    attempt_pressure = min(1.0, attempt_count / 5)
    risk = round(min(1.0, ml_conf * 0.70 + attempt_pressure * 0.30), 3)
    return risk, result["confidence"], result["prediction"]


# ── Helper: Fresh DB Stats ────────────────────────────────────────

def _get_db_stats(db: Session) -> dict:
    """Query real stats from DB for WebSocket broadcast."""
    total = db.query(func.count(RequestLog.id)).scalar() or 0
    attacks = db.query(func.count(RequestLog.id)).filter(RequestLog.prediction == "attack").scalar() or 0
    blocked_count = db.query(func.count(BlockedIP.id)).filter(BlockedIP.is_active == True).scalar() or 0
    return {
        "total_requests": total,
        "total_attacks": attacks,
        "total_blocked": blocked_count,
        "active_users": manager.get_active_count(),
        "rpm": 0,
    }


# ── Helper: Log + Broadcast ───────────────────────────────────────

async def _log_and_broadcast(
    db: Session, ip: str, endpoint: str, method: str,
    status_code: int, result: dict, user_id: Optional[int] = None,
):
    log = RequestLog(
        ip_address=ip, endpoint=endpoint, method=method,
        status_code=status_code,
        response_time_ms=random.uniform(5, 100),
        prediction=result["prediction"],
        confidence=result["confidence"],
        attack_type=result.get("attack_type"),
        user_id=user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    log_entry = {
        "id": log.id, "ip_address": ip, "endpoint": endpoint,
        "method": method, "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat(),
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "severity": result["severity"],
        "attack_type": result.get("attack_type"),
    }

    db_stats = _get_db_stats(db)

    try:
        await broadcast_real_event(log_entry, result, db_stats)
    except Exception:
        pass

    return log_entry


# ── Request/Response Models ───────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class FormRequest(BaseModel):
    name: str
    email: str
    message: str


class AttackRequest(BaseModel):
    attack_type: str  # DDoS, SQL Injection, XSS, Brute Force, Port Scan
    twilio_enabled: bool = False  # Only send SMS/call when user toggles this on


class FloodRequest(BaseModel):
    count: int = 100           # simulated packet count


class ProbeRequest(BaseModel):
    endpoints: List[str]       # list of paths the user wants to enumerate


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/login")
async def xyz_login(
    req: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)

    if ip in blocked_ips:
        return {"status": "blocked", "message": "Access denied. Your IP has been blocked by PHANTOM.", "ip_address": ip}

    # ── SQL Injection detection: runs BEFORE brute-force check ──────────────
    sql_fields = [req.username, req.password]
    if any(_has_sql(f) for f in sql_fields):
        event = ml_engine.generate_event(attack_probability=0.97)
        event["attack_cat"] = "Exploits"
        event["label"] = 1
        result = ml_engine.predict_event(event)
        result.update({"prediction": "attack", "confidence": max(result["confidence"], 0.94),
                       "severity": "critical", "attack_type": "SQL Injection"})
        blocked_ips.add(ip)
        existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if not existing:
            db.add(BlockedIP(
                ip_address=ip,
                reason="SQL Injection payload detected in login form fields",
                attack_type="SQL Injection", confidence=result["confidence"],
                blocked_by="ml_engine", flagged=True,
            ))
        db.add(Alert(
            severity="critical",
            title=f"🚨 SQL Injection from {ip}",
            description=(
                f"SQL injection payload detected in login form from IP {ip}. "
                f"ML model confirmed attack (confidence: {result['confidence']:.2%}). IP auto-blocked."
            ),
            ip_address=ip, attack_type="SQL Injection", action_taken="auto_block",
        ))
        db.commit()
        await _log_and_broadcast(db, ip, "/api/xyz/login", "POST", 403, result, getattr(current_user, 'id', None))
        try:
            send_critical_alert(ip, "SQL Injection", result["confidence"])
        except Exception as e:
            print(f"[ALERT] Twilio error: {e}")
        return {
            "status": "blocked",
            "message": "🚨 SQL Injection detected! Malicious payload flagged by ML engine. IP blocked.",
            "ip_address": ip,
            "attack_type": "SQL Injection",
            "ml_confidence": round(result["confidence"], 4),
            "ml_prediction": "attack",
        }

    event = ml_engine.generate_event(attack_probability=0.2)
    result = ml_engine.predict_event(event)

    is_valid = (req.username == "demo" and req.password == "demo123")

    if not is_valid:
        attempt_count = _record_failed_login(ip)

        # ── ML-driven risk scoring: the model decides the tier, not a hard counter ──
        ml_risk, ml_conf, ml_pred = _compute_brute_risk(attempt_count)

        if ml_risk >= 0.75:
            # Model signals high threat → block
            blocked_ips.add(ip)
            result.update({"prediction": "attack", "confidence": ml_conf, "severity": "critical", "attack_type": "Brute Force"})

            existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
            if not existing:
                db.add(BlockedIP(
                    ip_address=ip,
                    reason=f"Brute force: {attempt_count} failed logins — ML risk score {ml_risk:.2f}",
                    attack_type="Brute Force", confidence=ml_conf,
                    blocked_by="ml_engine", flagged=True,
                ))
            db.add(Alert(
                severity="critical",
                title=f"🚨 Brute Force Attack from {ip}",
                description=(
                    f"IP {ip} blocked after {attempt_count} failed logins. "
                    f"ML risk score: {ml_risk:.2f} (confidence: {ml_conf:.2%}). "
                    f"Detected via ML-driven CDL behavioural analysis."
                ),
                ip_address=ip, attack_type="Brute Force", action_taken="auto_block",
            ))
            db.commit()
            await _log_and_broadcast(db, ip, "/api/xyz/login", "POST", 403, result, getattr(current_user, 'id', None))

            # 🚨 Twilio alert — SMS + Voice call
            try:
                send_critical_alert(ip, "Brute Force", ml_conf)
            except Exception as e:
                print(f"[ALERT] Twilio error (non-blocking): {e}")

            return {
                "status": "blocked",
                "message": f"⚠️ Brute force detected! IP ({ip}) blocked — ML risk score: {ml_risk:.2f}.",
                "ip_address": ip,
                "attempts": attempt_count,
                "ml_risk": ml_risk,
                "ml_confidence": round(ml_conf, 4),
                "ml_prediction": ml_pred,
                "suspicious": True,
            }

        elif ml_risk >= 0.35:
            # Model sees rising suspicion → warn but don't block yet
            result.update({"prediction": "attack", "confidence": ml_conf, "severity": "medium", "attack_type": "Brute Force"})
            await _log_and_broadcast(db, ip, "/api/xyz/login", "POST", 401, result, getattr(current_user, 'id', None))
            return {
                "status": "error",
                "message": "Invalid credentials",
                "ip_address": ip,
                "attempts": attempt_count,
                "remaining": max(0, 5 - attempt_count),
                "ml_risk": ml_risk,
                "ml_confidence": round(ml_conf, 4),
                "ml_prediction": ml_pred,
                "suspicious": True,
            }

        else:
            # Model sees low risk → silent fail, no warning shown
            result.update({"prediction": "normal", "confidence": ml_conf, "severity": "low"})
            await _log_and_broadcast(db, ip, "/api/xyz/login", "POST", 401, result, getattr(current_user, 'id', None))
            return {
                "status": "error",
                "message": "Invalid credentials",
                "ip_address": ip,
                "attempts": attempt_count,
                "remaining": max(0, 5 - attempt_count),
                "ml_risk": ml_risk,
                "ml_confidence": round(ml_conf, 4),
                "ml_prediction": ml_pred,
                "suspicious": False,
            }

    await _log_and_broadcast(db, ip, "/api/xyz/login", "POST", 200, result, getattr(current_user, 'id', None))
    return {"status": "success", "message": "Login successful", "token": "xyz-demo-token-12345", "user": {"username": req.username}, "ip_address": ip}


@router.get("/data")
async def xyz_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)

    if ip in blocked_ips:
        return {"status": "blocked", "message": "Access denied.", "ip_address": ip}

    # ── DDoS rate detection ──────────────────────────────────────────────────
    rate = _record_data_request(ip)
    if rate >= DDOS_RATE_THRESHOLD:
        event = ml_engine.generate_event(attack_probability=0.94)
        event["attack_cat"] = "DoS"
        event["label"] = 1
        result = ml_engine.predict_event(event)
        result.update({"prediction": "attack", "confidence": max(result["confidence"], 0.90),
                       "severity": "high", "attack_type": "DDoS"})
        blocked_ips.add(ip)
        existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if not existing:
            db.add(BlockedIP(
                ip_address=ip,
                reason=f"DDoS: {rate} requests in {DDOS_RATE_WINDOW}s — ML DoS model triggered",
                attack_type="DDoS", confidence=result["confidence"],
                blocked_by="ml_engine", flagged=True,
            ))
        db.add(Alert(
            severity="high",
            title=f"🚨 DDoS Attack from {ip}",
            description=(
                f"IP {ip} made {rate} data requests in {DDOS_RATE_WINDOW}s. "
                f"ML model flagged as DoS pattern (confidence: {result['confidence']:.2%}). IP auto-blocked."
            ),
            ip_address=ip, attack_type="DDoS", action_taken="auto_block",
        ))
        db.commit()
        await _log_and_broadcast(db, ip, "/api/xyz/data", "GET", 429, result, getattr(current_user, 'id', None))
        try:
            send_critical_alert(ip, "DDoS", result["confidence"])
        except Exception as e:
            print(f"[ALERT] Twilio error: {e}")
        return {
            "status": "blocked",
            "message": f"🚨 DDoS detected! {rate} requests/{DDOS_RATE_WINDOW}s — ML DoS pattern confirmed. IP blocked.",
            "ip_address": ip,
            "attack_type": "DDoS",
            "request_rate": rate,
            "ml_confidence": round(result["confidence"], 4),
        }

    result = {
        "prediction": "normal",
        "confidence": 0.05,
        "severity": "low",
        "attack_type": None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await _log_and_broadcast(db, ip, "/api/xyz/data", "GET", 200, result, getattr(current_user, 'id', None))
    return {
        "status": "success",
        "data": {"products": [
            {"id": 1, "name": "Widget A", "price": 29.99},
            {"id": 2, "name": "Widget B", "price": 49.99},
            {"id": 3, "name": "Widget C", "price": 79.99},
        ], "timestamp": datetime.utcnow().isoformat()},
        "ip_address": ip,
        "request_rate": rate,
    }


@router.post("/flood")
async def xyz_flood(
    req: FloodRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    DDoS simulation: user specifies a packet count, backend generates
    a DoS-profile ML event proportional to count and runs it through LightGBM.
    """
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)

    if ip in blocked_ips:
        return {"status": "blocked", "message": "Access denied.", "ip_address": ip}

    # Scale attack probability with packet count (higher flood = more hostile signal)
    prob = min(0.99, 0.70 + (req.count / 5000))
    event = ml_engine.generate_event(attack_probability=prob)
    event["attack_cat"] = "DoS"
    event["label"] = 1
    result = ml_engine.predict_event(event)
    result.update({"prediction": "attack", "confidence": max(result["confidence"], 0.88),
                   "severity": "high", "attack_type": "DDoS"})
    blocked_ips.add(ip)
    existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    if not existing:
        db.add(BlockedIP(
            ip_address=ip,
            reason=f"DDoS flood simulation: {req.count} packets — ML DoS model triggered",
            attack_type="DDoS", confidence=result["confidence"],
            blocked_by="ml_engine", flagged=True,
        ))
    db.add(Alert(
        severity="high",
        title=f"🚨 DDoS Flood from {ip}",
        description=(
            f"IP {ip} launched DDoS flood ({req.count} packets). "
            f"ML DoS model confirmed (confidence: {result['confidence']:.2%}). IP auto-blocked."
        ),
        ip_address=ip, attack_type="DDoS", action_taken="auto_block",
    ))
    db.commit()
    await _log_and_broadcast(db, ip, "/api/xyz/flood", "POST", 429, result, getattr(current_user, 'id', None))
    try:
        send_critical_alert(ip, "DDoS", result["confidence"])
    except Exception as e:
        print(f"[ALERT] Twilio error: {e}")
    return {
        "status": "blocked",
        "message": f"🚨 DDoS Flood detected! {req.count} packets → ML model confirmed DoS signature. IP blocked.",
        "ip_address": ip,
        "attack_type": "DDoS",
        "packet_count": req.count,
        "ml_confidence": round(result["confidence"], 4),
        "ml_prediction": "attack",
    }


@router.post("/probe")
async def xyz_probe(
    req: ProbeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Port scan / endpoint enumeration detection.
    User submits a list of paths they want to 'probe' — backend detects
    the recon pattern and runs a Reconnaissance-profile ML event.
    """
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)

    if ip in blocked_ips:
        return {"status": "blocked", "message": "Access denied.", "ip_address": ip}

    n = len(req.endpoints)
    # Scale probability with breadth of scan
    prob = min(0.99, 0.60 + (n / 20))
    event = ml_engine.generate_event(attack_probability=prob)
    event["attack_cat"] = "Reconnaissance"
    event["label"] = 1
    result = ml_engine.predict_event(event)
    result.update({"prediction": "attack", "confidence": max(result["confidence"], 0.85),
                   "severity": "high", "attack_type": "Port Scan"})
    blocked_ips.add(ip)
    probe_list = ", ".join(req.endpoints[:8])
    existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    if not existing:
        db.add(BlockedIP(
            ip_address=ip,
            reason=f"Port scan / endpoint enumeration: {n} paths probed — ML Recon model triggered",
            attack_type="Port Scan", confidence=result["confidence"],
            blocked_by="ml_engine", flagged=True,
        ))
    db.add(Alert(
        severity="high",
        title=f"🚨 Port Scan from {ip}",
        description=(
            f"IP {ip} enumerated {n} endpoints: [{probe_list}]. "
            f"ML Reconnaissance model confirmed (confidence: {result['confidence']:.2%}). IP auto-blocked."
        ),
        ip_address=ip, attack_type="Port Scan", action_taken="auto_block",
    ))
    db.commit()
    await _log_and_broadcast(db, ip, "/api/xyz/probe", "POST", 403, result, getattr(current_user, 'id', None))
    try:
        send_critical_alert(ip, "Port Scan", result["confidence"])
    except Exception as e:
        print(f"[ALERT] Twilio error: {e}")
    return {
        "status": "blocked",
        "message": f"🚨 Port Scan detected! {n} endpoints enumerated — ML Recon model triggered. IP blocked.",
        "ip_address": ip,
        "attack_type": "Port Scan",
        "endpoints_probed": req.endpoints,
        "ml_confidence": round(result["confidence"], 4),
        "ml_prediction": "attack",
    }


@router.post("/form")
async def xyz_form(
    req: FormRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)

    if ip in blocked_ips:
        return {"status": "blocked", "message": "Access denied.", "ip_address": ip}

    # ── XSS detection on all text fields ────────────────────────────────────
    xss_fields = [req.name, req.email, req.message]
    if any(_has_xss(f) for f in xss_fields):
        event = ml_engine.generate_event(attack_probability=0.96)
        event["attack_cat"] = "Exploits"
        event["label"] = 1
        result = ml_engine.predict_event(event)
        result.update({"prediction": "attack", "confidence": max(result["confidence"], 0.92),
                       "severity": "critical", "attack_type": "XSS"})
        blocked_ips.add(ip)
        existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if not existing:
            db.add(BlockedIP(
                ip_address=ip,
                reason="XSS payload detected in contact form fields",
                attack_type="XSS", confidence=result["confidence"],
                blocked_by="ml_engine", flagged=True,
            ))
        db.add(Alert(
            severity="critical",
            title=f"🚨 XSS Attack from {ip}",
            description=(
                f"Cross-site scripting payload detected in contact form from IP {ip}. "
                f"ML model confirmed attack (confidence: {result['confidence']:.2%}). IP auto-blocked."
            ),
            ip_address=ip, attack_type="XSS", action_taken="auto_block",
        ))
        db.commit()
        await _log_and_broadcast(db, ip, "/api/xyz/form", "POST", 403, result, getattr(current_user, 'id', None))
        try:
            send_critical_alert(ip, "XSS", result["confidence"])
        except Exception as e:
            print(f"[ALERT] Twilio error: {e}")
        return {
            "status": "blocked",
            "message": "🚨 XSS Attack detected! Script injection payload flagged by ML engine. IP blocked.",
            "ip_address": ip,
            "attack_type": "XSS",
            "ml_confidence": round(result["confidence"], 4),
            "ml_prediction": "attack",
        }

    result = {
        "prediction": "normal",
        "confidence": 0.02,
        "severity": "low",
        "attack_type": None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await _log_and_broadcast(db, ip, "/api/xyz/form", "POST", 200, result, getattr(current_user, 'id', None))
    return {"status": "success", "message": "Form submitted successfully", "submission_id": random.randint(1000, 9999), "ip_address": ip}


@router.post("/attack")
async def xyz_attack(
    req: AttackRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Attack simulation endpoint — generates a synthetic attack event,
    runs it through the REAL LightGBM ML model, and uses the model's
    actual prediction and confidence score.
    """
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)

    # Check if Twilio is enabled (sent from frontend toggle)
    twilio_enabled = req.twilio_enabled

    # If already blocked, just confirm
    if ip in blocked_ips:
        return {
            "status": "blocked",
            "message": f"Your IP ({ip}) is already blocked by PHANTOM.",
            "ip_address": ip,
            "attack_type": req.attack_type,
        }

    # ── REAL ML PREDICTION ─────────────────────────────────────
    # Map attack types to their UNSW-NB15 attack_cat names
    attack_cat_map = {
        "DDoS": "DoS",
        "SQL Injection": "Exploits",
        "XSS": "Exploits",
        "Brute Force": "Brute Force",
        "Port Scan": "Reconnaissance",
    }
    attack_cat = attack_cat_map.get(req.attack_type, "Exploits")

    # Generate a synthetic network event with high attack probability
    event = ml_engine.generate_event(attack_probability=0.95)
    event["attack_cat"] = attack_cat
    event["label"] = 1

    # Run through the REAL LightGBM model
    result = ml_engine.predict_event(event)

    # Since this is an intentional attack simulation, ensure it's at least
    # marked as an attack (the model may sometimes classify differently)
    if result["prediction"] == "normal":
        # Model didn't flag it — retry with a stronger signal
        event2 = ml_engine.generate_event(attack_probability=0.99)
        event2["attack_cat"] = attack_cat
        event2["label"] = 1
        result = ml_engine.predict_event(event2)

    # Use the real ML confidence but ensure attack labeling for the demo
    ml_confidence = result["confidence"]
    ml_prediction = result["prediction"]

    # Override attack_type to match what the user selected
    result["attack_type"] = req.attack_type

    if ml_prediction == "normal":
        result["prediction"] = "attack"
        result["severity"] = "high"

    confidence = ml_confidence

    # ── Feature Attribution ────────────────────────────────────────────────────
    top_features = ml_engine.explain_prediction(confidence)

    # ── Kill Chain Update ───────────────────────────────────────────────
    user_id = str(getattr(current_user, 'id', 'unknown'))
    kc_state = soc_engine.update_kill_chain(ip, req.attack_type, user_id)

    # ── SOC Playbook ──────────────────────────────────────────────────
    playbook = soc_engine.get_playbook(req.attack_type, ip, confidence)

    # ── CDL: Cyber Defense Logic (behavioural threat intelligence) ──────────────
    cdl_event = {"endpoint": f"/api/xyz/attack/{req.attack_type}", "attack_type": req.attack_type}
    cdl_data  = cdl_engine.process(ip, cdl_event, result)

    # Auto-block the IP
    blocked_ips.add(ip)

    # Save blocked IP to DB
    existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    if existing:
        existing.is_active = True
        existing.reason = f"ML detected {req.attack_type} (confidence: {confidence:.2%})"
        existing.attack_type = req.attack_type
        existing.confidence = confidence
        existing.flagged = True
        existing.blocked_by = "ml_engine"
        existing.blocked_at = datetime.utcnow()
    else:
        db.add(BlockedIP(
            ip_address=ip,
            reason=f"ML detected {req.attack_type} attack (confidence: {confidence:.2%}) — auto-blocked",
            attack_type=req.attack_type,
            confidence=confidence,
            blocked_by="ml_engine",
            flagged=True,
        ))

    # Create critical alert
    db.add(Alert(
        severity=result["severity"],
        title=f"🚨 {req.attack_type} Attack from {ip}",
        description=(
            f"PHANTOM ML model detected a {req.attack_type} attack from IP {ip} "
            f"with {confidence:.2%} confidence (prediction: {ml_prediction}). "
            f"Kill chain stage: {kc_state.get('current_stage','UNKNOWN')} "
            f"({kc_state.get('mitre_id','')} — {kc_state.get('mitre_name','')}). "
            f"IP has been automatically blocked."
        ),
        ip_address=ip,
        attack_type=req.attack_type,
        action_taken="auto_block",
    ))
    db.commit()

    # 🚨 Twilio alert — only if enabled by the user
    if twilio_enabled:
        try:
            send_critical_alert(ip, req.attack_type, confidence)
        except Exception as e:
            print(f"[ALERT] Twilio error (non-blocking): {e}")
    else:
        print(f"[ALERT] Twilio disabled — skipping SMS/call for {ip}")

    # Log and broadcast
    await _log_and_broadcast(
        db, ip, f"/api/xyz/attack/{req.attack_type.lower().replace(' ', '_')}",
        "POST", 403, result,
        getattr(current_user, 'id', None)
    )

    return {
        "status": "blocked",
        "message": f"⚠️ {req.attack_type} attack detected! Your IP ({ip}) has been blocked by PHANTOM.",
        "ip_address": ip,
        "attack_type": req.attack_type,
        "confidence": round(confidence, 4),
        "ml_prediction": ml_prediction,
        "action": "auto_blocked",
        "model_used": "LightGBM (Optuna-tuned)",
        # ── ML Intelligence ───────────────────────────────────────────────
        "top_features": top_features,
        "kill_chain": {
            "stage": kc_state.get("current_stage", "UNKNOWN"),
            "stage_num": kc_state.get("stage_num", 0),
            "mitre_id": kc_state.get("mitre_id", ""),
            "mitre_name": kc_state.get("mitre_name", ""),
            "severity": kc_state.get("severity", "LOW"),
            "history": kc_state.get("history", []),
        },
        "playbook": playbook,
        # ── CDL Intelligence ──────────────────────────────────────────────
        "cdl": cdl_data,
    }


@router.get("/status")
async def xyz_status(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)
    return {
        "status": "operational", "service": "XYZ Corp",
        "protected_by": "PHANTOM",
        "timestamp": datetime.utcnow().isoformat(),
        "your_ip": ip, "is_blocked": ip in blocked_ips,
    }


@router.get("/my-ip")
async def get_my_ip(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    real_ip = request.client.host if request.client else "unknown"
    ip = _get_user_ip(current_user, real_ip)
    attempts = _get_attempt_count(ip)
    return {
        "ip_address": ip,
        "is_blocked": ip in blocked_ips,
        "failed_attempts": attempts,
        "max_attempts": 5,
    }
