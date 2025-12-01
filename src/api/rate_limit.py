"""
Rate limiting utilities using Redis
"""

import redis
from fastapi import HTTPException, Request
from datetime import datetime
from src.core.config import get_settings

settings = get_settings()

try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception:
    redis_client = None


async def rate_limit(
    request: Request,
    max_requests: int = 60,
    window: int = 60,
    key_prefix: str = "rate_limit",
):
    """
    Rate limit requests using Redis

    Args:
        request: FastAPI request object
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
        key_prefix: Redis key prefix

    Raises:
        HTTPException: If rate limit is exceeded
    """
    if not redis_client:
        # Skip rate limiting if Redis is not available
        return

    # Use client IP as identifier
    client_ip = request.client.host if request.client else "unknown"

    # Create time-based key (per minute)
    current_minute = datetime.now().strftime("%Y%m%d%H%M")
    key = f"{key_prefix}:{client_ip}:{current_minute}"

    try:
        # Increment counter
        current = redis_client.incr(key)

        # Set expiration on first request
        if current == 1:
            redis_client.expire(key, window)

        # Check if limit exceeded
        if current > max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window} seconds",
                headers={"Retry-After": str(window)},
            )

    except redis.RedisError:
        # If Redis fails, allow the request
        pass


async def get_rate_limit_info(request: Request, key_prefix: str = "rate_limit"):
    """
    Get current rate limit status for a client

    Args:
        request: FastAPI request object
        key_prefix: Redis key prefix

    Returns:
        Dictionary with rate limit info
    """
    if not redis_client:
        return {"available": True, "remaining": None}

    client_ip = request.client.host if request.client else "unknown"
    current_minute = datetime.now().strftime("%Y%m%d%H%M")
    key = f"{key_prefix}:{client_ip}:{current_minute}"

    try:
        current = redis_client.get(key)
        current = int(current) if current else 0
        return {"current": current, "key": key}
    except redis.RedisError:
        return {"available": True, "remaining": None}
