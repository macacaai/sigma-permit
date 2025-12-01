from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import os
from typing import Optional

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "auth": {"requests": 5, "window": 60},       # 5 auth requests per minute
            "token": {"requests": 10, "window": 60},     # 10 token requests per minute
        }

    def is_allowed(self, key: str, limit_type: str = "default") -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        limit = self.limits.get(limit_type, self.limits["default"])

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key]
                            if now - req_time < limit["window"]]

        # Check if under limit
        if len(self.requests[key]) >= limit["requests"]:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_client_key(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Try to get user ID from token if available
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # In a real implementation, you'd decode the token to get user ID
        # For now, use a hash of the token as key
        import hashlib
        token_hash = hashlib.sha256(auth_header[7:].encode()).hexdigest()[:16]
        return f"user:{token_hash}"

    # Fallback to IP address
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for certain paths
    skip_paths = ["/docs", "/redoc", "/openapi.json", "/metrics", "/health"]
    if any(request.url.path.startswith(path) for path in skip_paths):
        return await call_next(request)

    client_key = get_client_key(request)

    # Determine limit type based on path
    limit_type = "default"
    if request.url.path.startswith("/api/auth"):
        limit_type = "auth"
    elif request.url.path.startswith("/oauth/v1/token"):
        limit_type = "token"

    if not rate_limiter.is_allowed(client_key, limit_type):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )

    response = await call_next(request)

    # Add rate limit headers
    limit = rate_limiter.limits[limit_type]
    remaining = max(0, limit["requests"] - len(rate_limiter.requests[client_key]))
    response.headers["X-RateLimit-Limit"] = str(limit["requests"])
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + limit["window"]))

    return response

# Dependency for custom rate limiting
def rate_limit(limit_type: str = "default"):
    """Dependency for custom rate limiting"""
    def rate_limit_dependency(request: Request):
        client_key = get_client_key(request)

        if not rate_limiter.is_allowed(client_key, limit_type):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        return True

    return rate_limit_dependency