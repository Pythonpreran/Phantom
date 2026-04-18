"""
PHANTOM — Authentication (JWT + bcrypt)
7 accounts: 1 admin, 2 companies (ABC/XYZ), 4 users (2 per company)
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_db, User

SECRET_KEY = "phantom-security-key-change-in-production-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    role: str = "user"
    company_name: Optional[str] = None
    company_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    user_id: int

class UserInfo(BaseModel):
    id: int
    email: str
    username: str
    role: str
    company_name: Optional[str] = None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_simulated_ip(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    return f"203.{int(h[:2],16)%200+10}.{int(h[2:4],16)%200+10}.{max(1, int(h[4:6],16)%254)}"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        return db.query(User).filter(User.id == user_id).first()
    except JWTError:
        return None


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*roles):
    async def checker(user: User = Depends(require_auth)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


def seed_defaults(db: Session):
    """
    Seed 7 accounts:
      1 admin
      2 companies: ABC Corp, XYZ Corp
      4 users: Alice & Bob (ABC), Sarah & Mike (XYZ)
    Also clears all blocked IPs for fresh demo.
    """
    defaults = [
        # Admin
        {"email": "admin@phantom.io", "username": "Admin", "password": "admin123",
         "role": "admin", "company_id": None, "company_name": None},
        # Companies
        {"email": "abc@company.com", "username": "ABC Corp", "password": "abc123",
         "role": "company", "company_id": "abc", "company_name": "ABC Corporation"},
        {"email": "xyz@company.com", "username": "XYZ Corp", "password": "xyz123",
         "role": "company", "company_id": "xyz", "company_name": "XYZ Corporation"},
        # ABC users
        {"email": "alice@abc.com", "username": "Alice Chen", "password": "alice123",
         "role": "user", "company_id": "abc", "company_name": "ABC Corporation"},
        {"email": "bob@abc.com", "username": "Bob Smith", "password": "bob123",
         "role": "user", "company_id": "abc", "company_name": "ABC Corporation"},
        # XYZ users
        {"email": "sarah@xyz.com", "username": "Sarah Johnson", "password": "sarah123",
         "role": "user", "company_id": "xyz", "company_name": "XYZ Corporation"},
        {"email": "mike@xyz.com", "username": "Mike Wilson", "password": "mike123",
         "role": "user", "company_id": "xyz", "company_name": "XYZ Corporation"},
    ]

    for d in defaults:
        existing = db.query(User).filter(User.email == d["email"]).first()
        if not existing:
            db.add(User(
                email=d["email"],
                username=d["username"],
                password_hash=hash_password(d["password"]),
                role=d["role"],
                company_name=d.get("company_name"),
                company_id=d.get("company_id"),
                simulated_ip=generate_simulated_ip(d["email"]),
                is_blocked=False,
            ))
        else:
            # Backfill and make sure nobody is blocked
            existing.is_blocked = False
            existing.company_id = d.get("company_id")
            if not existing.simulated_ip:
                existing.simulated_ip = generate_simulated_ip(d["email"])

    db.commit()

    # Unblock ALL IPs in blocked_ips table
    from .database import BlockedIP
    db.query(BlockedIP).update({"is_active": False})
    db.commit()
