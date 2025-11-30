"""
Authentication utilities: JWT token creation/verification, password hashing, OTP management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
import re
import hmac
from .config import settings
from .utils.otp_manager import generate_otp_code, generate_otp_token, validate_otp_token

# Security configuration from environment variables
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token
    Returns payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


# OTP and Reset Token Functions

def create_otp(username: str, purpose: str, db_session = None) -> Dict[str, str]:
    """
    Create OTP code and token for user
    
    Args:
        username: Target username
        purpose: Purpose of OTP (registration, password_reset, email_change)
        db_session: Database session (not used, kept for consistency)
    
    Returns:
        Dict: {"otp_code": "123456", "otp_token": "jwt_token"}
    """
    otp_code = generate_otp_code()
    otp_token = generate_otp_token(username, purpose, otp_code, db_session)
    
    return {
        "otp_code": otp_code,
        "otp_token": otp_token
    }


def verify_otp(
    otp_code: str,
    otp_token: str,
    username: str,
    purpose: str
) -> Dict[str, Union[bool, str, int]]:
    """
    Verify OTP code and token
    
    Args:
        otp_code: OTP code provided by user
        otp_token: JWT token from localStorage
        username: Target username
        purpose: Expected purpose
    
    Returns:
        Dict: {
            "success": bool,
            "remaining_trials": int,
            "updated_token": str (optional),
            "message": str
        }
    """
    return validate_otp_token(otp_code, otp_token, username, purpose)


def create_reset_token(username: str, purpose: str = "password_reset") -> str:
    """
    Create reset token for password recovery
    
    Args:
        username: Target username
        purpose: Purpose of reset token
    
    Returns:
        str: JWT reset token
    """
    expire_time = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": username,
        "purpose": purpose,
        "iat": datetime.utcnow(),
        "exp": expire_time,
        "type": "reset"
    }
    
    token = jwt.encode(payload, settings.SECRET_RESET_KEY, algorithm=ALGORITHM)
    return token


def verify_reset_token(token: str) -> Optional[dict]:
    """
    Verify and decode reset token
    
    Args:
        token: JWT reset token
    
    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_RESET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload
    except JWTError:
        return None


# Password Validation Functions

def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """
    Validate password strength according to security requirements
    
    Args:
        password: Plain password to validate
    
    Returns:
        Dict: {
            "valid": bool,
            "message": str,
            "errors": list[str]
        }
    """
    errors = []
    
    # Minimum length
    if len(password) < 8:
        errors.append("Mật khẩu phải có ít nhất 8 ký tự")
    
    # Uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Mật khẩu phải có ít nhất 1 chữ cái viết hoa")
    
    # Lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Mật khẩu phải có ít nhất 1 chữ cái viết thường")
    
    # Number
    if not re.search(r'\d', password):
        errors.append("Mật khẩu phải có ít nhất 1 chữ số")
    
    # Special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Mật khẩu phải có ít nhất 1 ký tự đặc biệt")
    
    if errors:
        return {
            "valid": False,
            "message": "Mật khẩu không đủ mạnh",
            "errors": errors
        }
    else:
        return {
            "valid": True,
            "message": "Mật khẩu đáp ứng yêu cầu bảo mật",
            "errors": []
        }


def validate_email_format(email: str) -> bool:
    """
    Simple email format validation
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if valid format, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(email_pattern, email))


def validate_username_format(username: str) -> dict:
    """
    Validate username format
    
    Args:
        username: Username to validate
    
    Returns:
        dict: Validation result with valid status and message
    """
    errors = []
    
    # Check length (3-32 characters)
    if len(username) < 3:
        errors.append("Username phải có ít nhất 3 ký tự")
    elif len(username) > 32:
        errors.append("Username không được vượt quá 32 ký tự")
    
    # Check valid characters (alphanumeric + underscore)
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username chỉ được chứa chữ cái, số và dấu gạch dưới")
    
    if errors:
        return {
            "valid": False,
            "message": "Username không hợp lệ",
            "errors": errors
        }
    else:
        return {
            "valid": True,
            "message": "Username hợp lệ",
            "errors": []
        }
