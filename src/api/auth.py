"""
Authentication and authorization utilities
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from src.core.config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API key from request header

    Args:
        api_key: API key from X-API-Key header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check against configured API keys
    valid_keys = getattr(settings, "api_keys", "").split(",")
    valid_keys = [key.strip() for key in valid_keys if key.strip()]

    if not valid_keys or api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return api_key


async def optional_api_key(api_key: str = Security(api_key_header)):
    """
    Optional API key verification (doesn't raise error if missing)

    Args:
        api_key: API key from X-API-Key header

    Returns:
        API key if present and valid, None otherwise
    """
    if not api_key:
        return None

    valid_keys = getattr(settings, "api_keys", "").split(",")
    valid_keys = [key.strip() for key in valid_keys if key.strip()]

    if api_key in valid_keys:
        return api_key

    return None
