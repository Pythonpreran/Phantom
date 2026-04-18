"""
PHANTOM — FastAPI Application Entry Point
Real-time AI-powered cybersecurity defense system.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

# Ensure parent dir is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from .database import init_db, SessionLocal, BlockedIP, get_db
from .auth import (
    seed_defaults, LoginRequest, RegisterRequest, TokenResponse,
    hash_password, verify_password, create_access_token, generate_simulated_ip
)
from .database import User
from .middleware import PhantomMiddleware, blocked_ips
from .realtime import manager
from .ml_engine import ml_engine

# Import routers
from .routes.logs import router as logs_router
from .routes.admin import router as admin_router
from .routes.company import router as company_router
from .routes.honeypot import router as honeypot_router
from .routes.validation import router as validation_router
from .routes.website import router as website_router
from .routes.soc import router as soc_router

# Security bearer for auth/me endpoint
security_bearer = HTTPBearer(auto_error=False)


# ── Lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n[PHANTOM] Initializing database...")
    init_db()

    # Seed default accounts
    db = SessionLocal()
    seed_defaults(db)

    # Load blocked IPs into memory
    blocked_records = db.query(BlockedIP).filter(BlockedIP.is_active == True).all()
    for b in blocked_records:
        blocked_ips.add(b.ip_address)
    print(f"[PHANTOM] Loaded {len(blocked_ips)} blocked IPs")
    db.close()

    print("[PHANTOM] Server ready — http://localhost:8000 (NO simulation — 100% real data)")

    # Pre-warm the SOC engine (kill chain tracker)
    from . import soc_engine as _soc
    print(f"[PHANTOM] SOC Engine ready — Kill Chain Tracker online")
    print("[PHANTOM] Default accounts:")
    print("  Admin:   admin@phantom.io / admin123")
    print("  Company: company@xyz.com / company123")
    print("  User:    user@example.com / user123")
    print("  User:    alice@example.com / alice123")
    print("  User:    bob@example.com / bob123\n")

    yield

    # Shutdown
    print("\n[PHANTOM] Shutting down...")


# ── App ────────────────────────────────────────────────────────────

app = FastAPI(
    title="PHANTOM",
    description="AI-Powered Real-Time Cybersecurity Defense System",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(PhantomMiddleware)

# Mount routers
app.include_router(logs_router)
app.include_router(admin_router)
app.include_router(company_router)
app.include_router(honeypot_router)
app.include_router(validation_router)
app.include_router(website_router)
app.include_router(soc_router)


# ── Auth endpoints ─────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        role=user.role,
        username=user.username,
        user_id=user.id
    )


@app.post("/api/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        company_name=req.company_name,
        simulated_ip=generate_simulated_ip(req.email),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        role=user.role,
        username=user.username,
        user_id=user.id
    )


@app.get("/api/auth/me")
async def get_me(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
):
    """Get current user info from token."""
    if credentials is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from jose import jwt as jose_jwt, JWTError
        from .auth import SECRET_KEY, ALGORITHM
        payload = jose_jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "company_name": user.company_name,
        }
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid token")


# ── WebSocket ──────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# ── Health check ───────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {
        "status": "operational",
        "service": "PHANTOM",
        "ml_model_loaded": ml_engine.model_loaded,
        "active_connections": manager.get_active_count(),
        "simulation": "disabled",
    }


# ── Full System Reset ─────────────────────────────────────────────

@app.post("/api/reset")
def full_system_reset(db: Session = Depends(get_db)):
    """
    Full system reset: unblock all IPs, clear all logs, alerts,
    honeypot events, validation tests. Re-seed default accounts.
    Accessible from the login page for demo purposes.
    """
    from .database import RequestLog, BlockedIP, Alert, HoneypotEvent, ValidationTest

    # Clear all tables
    db.query(RequestLog).delete()
    db.query(BlockedIP).delete()
    db.query(Alert).delete()
    db.query(HoneypotEvent).delete()
    db.query(ValidationTest).delete()
    db.commit()

    # Clear in-memory blocked IPs
    blocked_ips.clear()

    # Re-seed default accounts (reset passwords, unblock users)
    seed_defaults(db)

    print("[PHANTOM] Full system reset completed — all logs cleared, IPs unblocked")

    return {
        "status": "success",
        "message": "System reset complete. All logs cleared, all IPs unblocked.",
    }


# ── Twilio Toggle ─────────────────────────────────────────────────

# Global in-memory toggle for Twilio alerts
_twilio_enabled = False


@app.get("/api/twilio/status")
def twilio_status():
    """Get current Twilio toggle state."""
    return {"enabled": _twilio_enabled}


@app.post("/api/twilio/toggle")
def twilio_toggle():
    """Toggle Twilio alerts on/off."""
    global _twilio_enabled
    _twilio_enabled = not _twilio_enabled
    state = "enabled" if _twilio_enabled else "disabled"
    print(f"[PHANTOM] Twilio alerts {state}")
    return {"enabled": _twilio_enabled, "message": f"Twilio alerts {state}"}


# ── Serve frontend static files ───────────────────────────────────

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

