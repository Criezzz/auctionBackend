"""
QR Token management utilities for payment tokens
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from fastapi import HTTPException, status
import secrets
import string

from ..models import PaymentToken, Payment
from ..config import settings


class PaymentTokenError(Exception):
    """Custom exception for payment token errors"""
    pass


def generate_payment_token(
    payment_id: int,
    user_id: int,
    amount: int,
    payment_type: str,  # "deposit" or "final_payment"
    db: Session
) -> Tuple[str, datetime]:
    """
    Generate JWT token with appropriate expiry time
    
    Args:
        payment_id: ID from Payment table
        user_id: User account ID
        amount: Payment amount in VND
        payment_type: "deposit" or "final_payment"
        db: Database session
    
    Returns:
        Tuple[str, datetime]: (token_string, expires_at_datetime)
    """
    # Determine expiry time
    if payment_type == "deposit":
        expiry_minutes = settings.DEPOSIT_TOKEN_EXPIRE_MINUTES
    else:  # final_payment
        expiry_minutes = settings.PAYMENT_TOKEN_EXPIRE_HOURS * 60
    
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    # Generate unique token string
    token_string = secrets.token_urlsafe(32)
    
    # Create JWT payload
    payload = {
        "token_id": None,  # Will be updated after database insertion
        "payment_id": payment_id,
        "user_id": user_id,
        "amount": amount,
        "payment_type": payment_type,
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow()
    }
    
    # Generate JWT token
    jwt_token = jwt.encode(
        payload,
        settings.SECRET_PAYMENT_TOKEN_KEY,
        algorithm="HS256"
    )
    
    # Create database record
    db_token = PaymentToken(
        token=jwt_token,
        payment_id=payment_id,
        user_id=user_id,
        amount=amount,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.utcnow()
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    # Update JWT payload with actual token_id
    payload["token_id"] = db_token.token_id
    jwt_token_updated = jwt.encode(
        payload,
        settings.SECRET_PAYMENT_TOKEN_KEY,
        algorithm="HS256"
    )
    
    # Update the token in database
    db_token.token = jwt_token_updated
    db.commit()
    
    return jwt_token_updated, expires_at


def verify_payment_token(token: str, db: Session) -> Dict:
    """
    Verify token validity
    
    Args:
        token: JWT token string
        db: Database session
    
    Returns:
        Dict with token data (payment_id, user_id, amount, payment_type)
    
    Raises:
        HTTPException: If invalid, expired, or already used
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_PAYMENT_TOKEN_KEY,
            algorithms=["HS256"]
        )
        
        token_id = payload.get("token_id")
        payment_id = payload.get("payment_id")
        user_id = payload.get("user_id")
        amount = payload.get("amount")
        payment_type = payload.get("payment_type")
        
        if not all([token_id, payment_id, user_id, amount, payment_type]):
            raise PaymentTokenError("Invalid token payload")
        
        # Get token from database
        db_token = db.query(PaymentToken).filter(
            PaymentToken.token_id == token_id,
            PaymentToken.token == token
        ).first()
        
        if not db_token:
            raise PaymentTokenError("Token not found")
        
        # Check if token is used
        if db_token.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token has already been used"
            )
        
        # Check if token is expired
        if db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token has expired"
            )
        
        # Verify payment exists and belongs to user
        payment = db.query(Payment).filter(
            Payment.payment_id == payment_id,
            Payment.user_id == user_id
        ).first()
        
        if not payment:
            raise PaymentTokenError("Associated payment not found")
        
        return {
            "token_id": token_id,
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "payment_type": payment_type,
            "payment": payment,
            "db_token": db_token
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token: {str(e)}"
        )
    except PaymentTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def invalidate_token(token: str, db: Session) -> bool:
    """
    Mark token as used
    
    Args:
        token: JWT token string
        db: Database session
    
    Returns:
        bool: True if successful
    """
    try:
        # Decode token to get token_id
        payload = jwt.decode(
            token,
            settings.SECRET_PAYMENT_TOKEN_KEY,
            algorithms=["HS256"]
        )
        
        token_id = payload.get("token_id")
        
        if not token_id:
            return False
        
        # Get and update token
        db_token = db.query(PaymentToken).filter(
            PaymentToken.token_id == token_id,
            PaymentToken.token == token
        ).first()
        
        if not db_token:
            return False
        
        db_token.is_used = True
        db_token.used_at = datetime.utcnow()
        db.commit()
        
        return True
        
    except JWTError:
        return False


def generate_qr_url(token: str, base_url: str = None) -> str:
    """
    Generate mock payment URL for QR code
    
    Args:
        token: JWT token string
        base_url: Base URL for callback (optional)
    
    Returns:
        str: URL for QR code
    """
    if base_url is None:
        base_url = settings.APP_URL
    
    return f"{base_url}/payments/qr-callback/{token}"


def get_token_status(token: str, db: Session) -> Dict:
    """
    Get token status information
    
    Args:
        token: JWT token string
        db: Database session
    
    Returns:
        Dict with token status
    """
    try:
        # Try to decode token to get basic info
        payload = jwt.decode(
            token,
            settings.SECRET_PAYMENT_TOKEN_KEY,
            algorithms=["HS256"],
            options={"verify_exp": False}  # Don't check expiry for status
        )
        
        token_id = payload.get("token_id")
        payment_id = payload.get("payment_id")
        user_id = payload.get("user_id")
        amount = payload.get("amount")
        payment_type = payload.get("payment_type")
        
        if not token_id:
            return {
                "valid": False,
                "error": "Invalid token format"
            }
        
        # Get token from database
        db_token = db.query(PaymentToken).filter(
            PaymentToken.token_id == token_id,
            PaymentToken.token == token
        ).first()
        
        if not db_token:
            return {
                "valid": False,
                "error": "Token not found"
            }
        
        # Check status
        if db_token.is_used:
            return {
                "valid": False,
                "error": "Token already used",
                "used_at": db_token.used_at.isoformat()
            }
        
        if db_token.expires_at < datetime.utcnow():
            return {
                "valid": False,
                "error": "Token expired",
                "expired_at": db_token.expires_at.isoformat()
            }
        
        # Calculate remaining time
        now = datetime.utcnow()
        if db_token.expires_at > now:
            remaining_seconds = int((db_token.expires_at - now).total_seconds())
            remaining_minutes = remaining_seconds // 60
            
            return {
                "valid": True,
                "payment_id": payment_id,
                "user_id": user_id,
                "amount": amount,
                "payment_type": payment_type,
                "expires_at": db_token.expires_at.isoformat(),
                "remaining_minutes": remaining_minutes,
                "remaining_seconds": remaining_seconds
            }
        else:
            return {
                "valid": False,
                "error": "Token expired",
                "expired_at": db_token.expires_at.isoformat()
            }
            
    except JWTError:
        return {
            "valid": False,
            "error": "Invalid token signature"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error checking token: {str(e)}"
        }