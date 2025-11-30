"""
Simple in-memory rate limiting utilities
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict
import time
import hashlib
from fastapi import HTTPException, status
from app.config import settings


# In-memory storage for rate limiting
_rate_limit_storage: Dict[str, Dict[str, datetime]] = defaultdict(dict)
_client_requests: Dict[str, list] = defaultdict(list)


def _get_client_identifier(client_ip: str, username: str = None) -> str:
    """
    Generate unique identifier for rate limiting
    
    Args:
        client_ip: Client IP address
        username: Username (optional)
    
    Returns:
        str: Unique identifier for rate limiting
    """
    identifier = client_ip
    if username:
        identifier += f":{username}"
    return hashlib.md5(identifier.encode()).hexdigest()[:8]


def _cleanup_old_entries():
    """Remove old entries from storage to prevent memory leaks"""
    current_time = datetime.utcnow()
    expired_keys = []
    
    for key, storage in _rate_limit_storage.items():
        for limit_type, last_request in storage.items():
            if current_time - last_request > timedelta(hours=1):
                expired_keys.append((key, limit_type))
    
    for key, limit_type in expired_keys:
        del _rate_limit_storage[key][limit_type]


def check_rate_limit(
    identifier: str,
    limit_type: str,
    max_attempts: int,
    window_minutes: int
) -> tuple[bool, dict]:
    """
    Check if request is within rate limits
    
    Args:
        identifier: Unique identifier for the client
        limit_type: Type of rate limit (login, register, otp_send, etc.)
        max_attempts: Maximum attempts allowed
        window_minutes: Time window in minutes
    
    Returns:
        tuple: (is_allowed, {
            "remaining": int,
            "reset_time": datetime,
            "message": str
        })
    """
    # DISABLED: Always allow
    return True, {
        "remaining": 9999,
        "reset_time": None,
        "message": "Rate limiting is disabled."
    }


def check_client_ip_rate_limit(
    client_ip: str,
    limit_type: str,
    max_attempts: int,
    window_minutes: int
) -> bool:
    """
    Check rate limit based on client IP
    
    Args:
        client_ip: Client IP address
        limit_type: Type of rate limit
        max_attempts: Maximum attempts
        window_minutes: Window in minutes
    
    Returns:
        bool: True if allowed, False if rate limited
    """
    # DISABLED: Always allow
    return True


def check_username_rate_limit(
    username: str,
    limit_type: str,
    max_attempts: int,
    window_minutes: int
) -> bool:
    """
    Check rate limit based on username
    
    Args:
        username: Username
        limit_type: Type of rate limit
        max_attempts: Maximum attempts
        window_minutes: Window in minutes
    
    Returns:
        bool: True if allowed, False if rate limited
    """
    # DISABLED: Always allow
    return True


def get_rate_limit_info(
    client_ip: str,
    username: str = None,
    limit_type: str = "default"
) -> Dict:
    """
    Get current rate limit information
    
    Args:
        client_ip: Client IP address
        username: Username (optional)
        limit_type: Type of rate limit
    
    Returns:
        Dict: Rate limit information
    """
    _cleanup_old_entries()
    
    if username:
        identifier = _get_client_identifier(client_ip, username)
    else:
        identifier = _get_client_identifier(client_ip)
    
    storage = _rate_limit_storage[identifier]
    last_request = storage.get(limit_type)
    
    if not last_request:
        return {
            "allowed": True,
            "remaining": "unlimited",
            "reset_time": None,
            "message": "Không có giới hạn hiện tại"
        }
    
    current_time = datetime.utcnow()
    time_since_last = (current_time - last_request).total_seconds() / 60
    
    return {
        "allowed": True,
        "remaining": "checking...",
        "reset_time": last_request + timedelta(minutes=15),  # Default 15 min window
        "message": f"Lần cuối cách đây {time_since_last:.1f} phút"
    }


def reset_rate_limit(
    client_ip: str,
    username: str = None,
    limit_type: str = "default"
):
    """
    Reset rate limit for specific identifier
    
    Args:
        client_ip: Client IP address
        username: Username (optional)
        limit_type: Type of rate limit to reset
    """
    if username:
        identifier = _get_client_identifier(client_ip, username)
    else:
        identifier = _get_client_identifier(client_ip)
    
    storage = _rate_limit_storage[identifier]
    storage.pop(limit_type, None)


class RateLimitError(HTTPException):
    """Custom exception for rate limit errors"""
    
    def __init__(self, detail: str, retry_after: Optional[int] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after) if retry_after else None}
        )


def rate_limit_decorator(
    limit_type: str,
    max_attempts: int,
    window_minutes: int,
    use_username: bool = False
):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit_type: Type of rate limit
        max_attempts: Maximum attempts
        window_minutes: Window in minutes
        use_username: Whether to use username for rate limiting
    
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from fastapi import Request
            from fastapi import Depends
            
            # Find request object in arguments
            request = None
            username = None
            current_user = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
                elif hasattr(arg, 'client'):
                    request = arg
            
            if request is None:
                # Try to get from kwargs
                request = kwargs.get('request')
            
            if request is None:
                # Try to get client IP from dependencies
                from fastapi import Request
                # Continue without rate limiting if request not found
                return await func(*args, **kwargs)
            
            client_ip = request.client.host if request.client else "unknown"
            
            # Get username if using username-based rate limiting
            if use_username:
                # Try to get from current user dependency
                for arg in args:
                    if hasattr(arg, 'username'):  # Assume this is the user model
                        username = arg.username
                        break
            
            # Check rate limit
            if username:
                is_allowed, info = check_rate_limit(
                    _get_client_identifier(client_ip, username),
                    limit_type, max_attempts, window_minutes
                )
            else:
                is_allowed, info = check_rate_limit(
                    _get_client_identifier(client_ip),
                    limit_type, max_attempts, window_minutes
                )
            
            if not is_allowed:
                retry_after = int((info["reset_time"] - datetime.utcnow()).total_seconds())
                raise RateLimitError(info["message"], retry_after)
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator