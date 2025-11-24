"""
OTP management utilities for generating and validating OTP tokens
"""
import random
import hmac
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from jose import jwt, JWTError
from app.config import settings


def generate_otp_code(length: int = 6) -> str:
    """
    Generate a random OTP code
    
    Args:
        length: Length of OTP code (default: 6)
    
    Returns:
        str: Random numeric OTP code
    """
    return ''.join(random.choices(string.digits, k=length))


def generate_otp_token(
    username: str, 
    purpose: str, 
    otp_code: str,
    db_session = None
) -> str:
    """
    Generate JWT token containing OTP code and metadata
    
    Args:
        username: Target username
        purpose: Purpose of OTP (registration, password_reset, email_change)
        otp_code: The OTP code to embed in token
        db_session: Database session (not used, kept for consistency)
    
    Returns:
        str: JWT token containing OTP and metadata
    """
    expire_time = datetime.utcnow() + timedelta(minutes=settings.OTP_TOKEN_EXPIRE_MINUTES)
    jti = f"{username}_{purpose}_{datetime.utcnow().timestamp()}"
    
    payload = {
        "sub": username,
        "otp": otp_code,
        "purpose": purpose,
        "iat": datetime.utcnow(),
        "exp": expire_time,
        "jti": jti,
        "trials": settings.OTP_MAX_TRIALS
    }
    
    token = jwt.encode(payload, settings.SECRET_OTP_KEY, algorithm=settings.ALGORITHM)
    return token


def validate_otp_token(
    otp_code: str,
    otp_token: str,
    username: str,
    purpose: str
) -> Optional[Dict]:
    """
    Validate OTP token and check OTP code
    
    Args:
        otp_code: OTP code provided by user
        otp_token: JWT token from localStorage
        username: Target username
        purpose: Expected purpose
    
    Returns:
        Dict: {
            "success": bool,
            "remaining_trials": int,
            "updated_token": str (if trials reduced),
            "message": str
        }
        Returns None if token is invalid/expired
    """
    try:
        # Decode token
        payload = jwt.decode(otp_token, settings.SECRET_OTP_KEY, algorithms=[settings.ALGORITHM])
        
        # Check expiration
        exp_timestamp = payload.get("exp")
        if not exp_timestamp or datetime.utcnow() > datetime.fromtimestamp(exp_timestamp):
            return {
                "success": False,
                "remaining_trials": 0,
                "updated_token": None,
                "message": "OTP token đã hết hạn. Vui lòng yêu cầu OTP mới."
            }
        
        # Check username
        if payload.get("sub") != username:
            return {
                "success": False,
                "remaining_trials": 0,
                "updated_token": None,
                "message": "Username không khớp với OTP token."
            }
        
        # Check purpose
        if payload.get("purpose") != purpose:
            return {
                "success": False,
                "remaining_trials": 0,
                "updated_token": None,
                "message": "Mục đích OTP không đúng."
            }
        
        # Check remaining trials
        trials = payload.get("trials", 0)
        if trials <= 0:
            return {
                "success": False,
                "remaining_trials": 0,
                "updated_token": None,
                "message": "Đã vượt quá số lần thử tối đa. Vui lòng yêu cầu OTP mới."
            }
        
        # Compare OTP codes using constant-time comparison
        stored_otp = payload.get("otp", "")
        if hmac.compare_digest(stored_otp, otp_code):
            # OTP is correct
            return {
                "success": True,
                "remaining_trials": trials,
                "updated_token": None,
                "message": "OTP xác minh thành công."
            }
        else:
            # OTP is wrong, decrement trials
            remaining_trials = trials - 1
            
            # If no trials left, return failure
            if remaining_trials <= 0:
                return {
                    "success": False,
                    "remaining_trials": 0,
                    "updated_token": None,
                    "message": "Đã vượt quá số lần thử tối đa. Vui lòng yêu cầu OTP mới."
                }
            
            # Generate new token with updated trials
            new_payload = payload.copy()
            new_payload["trials"] = remaining_trials
            
            # Remove exp and iat to reset them
            new_payload.pop("exp", None)
            new_payload.pop("iat", None)
            
            # Add new expiration
            new_payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.OTP_TOKEN_EXPIRE_MINUTES)
            new_payload["iat"] = datetime.utcnow()
            
            updated_token = jwt.encode(new_payload, settings.SECRET_OTP_KEY, algorithm=settings.ALGORITHM)
            
            return {
                "success": False,
                "remaining_trials": remaining_trials,
                "updated_token": updated_token,
                "message": f"Mã OTP không đúng. Bạn còn {remaining_trials} lần thử."
            }
            
    except JWTError:
        return {
            "success": False,
            "remaining_trials": 0,
            "updated_token": None,
            "message": "OTP token không hợp lệ."
        }
    except Exception as e:
        return {
            "success": False,
            "remaining_trials": 0,
            "updated_token": None,
            "message": f"Lỗi xác minh OTP: {str(e)}"
        }


def decode_otp_token(otp_token: str) -> Optional[Dict]:
    """
    Decode OTP token without validation
    
    Args:
        otp_token: JWT token to decode
    
    Returns:
        Dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(otp_token, settings.SECRET_OTP_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_status(otp_token: str) -> Dict:
    """
    Get status of OTP token without checking OTP code
    
    Args:
        otp_token: JWT token from localStorage
    
    Returns:
        Dict: {
            "valid": bool,
            "expired": bool,
            "remaining_trials": int,
            "purpose": str,
            "username": str,
            "expires_at": datetime
        }
    """
    payload = decode_otp_token(otp_token)
    
    if not payload:
        return {
            "valid": False,
            "expired": True,
            "remaining_trials": 0,
            "purpose": None,
            "username": None,
            "expires_at": None
        }
    
    exp_timestamp = payload.get("exp")
    now_timestamp = datetime.utcnow().timestamp()
    
    is_expired = not exp_timestamp or now_timestamp > exp_timestamp
    expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
    
    return {
        "valid": not is_expired,
        "expired": is_expired,
        "remaining_trials": payload.get("trials", 0),
        "purpose": payload.get("purpose"),
        "username": payload.get("sub"),
        "expires_at": expires_at
    }