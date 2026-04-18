"""
PHANTOM — Middleware (Request Logging, IP Blocking, Rate Limiting)
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_rate_limited(self, ip: str) -> bool:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Clean old entries
        self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]

        if len(self.requests[ip]) >= self.max_requests:
            return True

        self.requests[ip].append(now)
        return False

    def get_count(self, ip: str) -> int:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
        return len(self.requests[ip])


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=500, window_seconds=60)

# Tighter rate limiter for login endpoint (brute force protection)
login_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

# Global set of blocked IPs (loaded from DB on startup)
blocked_ips: set = set()


class PhantomMiddleware(BaseHTTPMiddleware):
    """Logs requests and checks for blocked IPs."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get client IP
        ip = request.client.host if request.client else "unknown"

        # Check blocked IPs (skip for internal/frontend routes)
        path = request.url.path
        if ip in blocked_ips and path.startswith("/api/xyz"):
            return Response(
                content='{"detail": "Access denied. Your IP has been blocked by PHANTOM.", "status": "blocked"}',
                status_code=403,
                media_type="application/json"
            )

        # Tighter rate limiting for login endpoint
        if path == "/api/xyz/login" and login_rate_limiter.is_rate_limited(ip):
            return Response(
                content='{"detail": "Too many login attempts. Please wait before trying again.", "status": "rate_limited"}',
                status_code=429,
                media_type="application/json"
            )

        # Check rate limiting for API routes
        if path.startswith("/api/") and rate_limiter.is_rate_limited(ip):
            return Response(
                content='{"detail": "Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json"
            )

        # Process the request
        response = await call_next(request)

        # Calculate response time
        process_time = (time.time() - start_time) * 1000

        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["X-Phantom-Status"] = "protected"

        return response
