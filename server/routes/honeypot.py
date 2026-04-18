"""
PHANTOM — Honeypot Routes
Fake vulnerable endpoints that log all attacker interactions.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..database import get_db, HoneypotEvent

router = APIRouter(prefix="/api/honeypot", tags=["honeypot"])


class HoneypotLoginRequest(BaseModel):
    username: str
    password: str


class HoneypotQueryRequest(BaseModel):
    query: Optional[str] = None
    search: Optional[str] = None
    id: Optional[str] = None


def _log_honeypot(db: Session, request: Request, event_type: str, payload: str, captured_data: str):
    """Log a honeypot interaction."""
    ip = request.client.host if request.client else "unknown"
    event = HoneypotEvent(
        ip_address=ip,
        endpoint=str(request.url.path),
        method=request.method,
        payload=payload,
        event_type=event_type,
        captured_data=captured_data,
    )
    db.add(event)
    db.commit()


@router.post("/login")
async def fake_login(
    req: HoneypotLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Fake login endpoint. Always fails but logs credentials.
    Designed to look like a real vulnerable login.
    """
    _log_honeypot(
        db, request,
        event_type="login_attempt",
        payload=json.dumps({"username": req.username, "password": req.password}),
        captured_data=f"Attacker tried credentials: {req.username}:{req.password}"
    )

    # Simulate a realistic but always-failing response
    return {
        "status": "error",
        "message": "Invalid credentials. Please try again.",
        "error_code": "AUTH_FAILED",
        "remaining_attempts": 2,  # Bait to keep trying
    }


@router.get("/api/users")
async def fake_users_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    """Fake users API that returns 'sensitive' data."""
    _log_honeypot(
        db, request,
        event_type="api_probe",
        payload="GET /api/users",
        captured_data="Attacker probed users endpoint"
    )

    return {
        "users": [
            {"id": 1, "name": "admin", "email": "admin@internal.xyz", "role": "admin"},
            {"id": 2, "name": "operator", "email": "ops@internal.xyz", "role": "operator"},
        ],
        "total": 2,
        "_debug": "database: users_prod_v2"  # Fake debug info as bait
    }


@router.get("/api/config")
async def fake_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """Fake config endpoint with 'leaked' information."""
    _log_honeypot(
        db, request,
        event_type="api_probe",
        payload="GET /api/config",
        captured_data="Attacker accessed config endpoint"
    )

    return {
        "database": {"host": "10.0.0.5", "port": 5432, "name": "production_db"},
        "api_key": "sk-fake-XXXXXXXXXXXXXXXXXXXX",
        "debug_mode": True,
    }


@router.post("/api/query")
async def fake_query(
    req: HoneypotQueryRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Fake query endpoint - captures SQL injection attempts."""
    payload_data = req.query or req.search or req.id or ""

    _log_honeypot(
        db, request,
        event_type="sql_injection",
        payload=json.dumps({"query": payload_data}),
        captured_data=f"Potential SQL injection payload: {payload_data}"
    )

    # Simulate a 'vulnerable' response
    return {
        "results": [],
        "query_time_ms": 145,
        "error": None,
    }


@router.api_route("/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def fake_admin_panel(
    path: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Catch-all fake admin panel."""
    body = ""
    try:
        body = (await request.body()).decode("utf-8", errors="replace")
    except Exception:
        pass

    _log_honeypot(
        db, request,
        event_type="admin_probe",
        payload=f"{request.method} /admin/{path} body={body[:500]}",
        captured_data=f"Attacker probed admin panel: /admin/{path}"
    )

    return {
        "status": "unauthorized",
        "message": "Admin authentication required",
        "login_url": "/api/honeypot/login"
    }
