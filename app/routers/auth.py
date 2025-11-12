"""
Authentication endpoints: login, refresh, me
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud, schemas
from ..database import SessionLocal
from ..auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dependency to get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = crud.get_account_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint: authenticate user and return JWT tokens
    
    POST /auth/login
    Body: { "username": "user123", "password": "secret" }
    Returns: { "access_token", "refresh_token", "token_type", "expires_in" }
    """
    # Authenticate user
    user = crud.authenticate_account(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated",
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # convert to seconds
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    refresh_data: schemas.RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh token endpoint: get new access token using refresh token
    
    POST /auth/refresh
    Body: { "refresh_token": "..." }
    Returns: { "access_token", "refresh_token", "token_type", "expires_in" }
    """
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Verify user still exists
    user = crud.get_account_by_username(db, username)
    if not user or not user.activated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not activated",
        )
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user = Depends(get_current_user)):
    """
    Get current user info endpoint
    
    GET /auth/me
    Headers: Authorization: Bearer <access_token>
    Returns: { "id", "username", "email", "role", ... }
    """
    return schemas.UserResponse(
        id=current_user.account_id,
        username=current_user.username,
        email=current_user.email,
        role="admin" if current_user.is_admin else "user",
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone_num=current_user.phone_num,
        activated=current_user.activated,
        is_authenticated=current_user.is_authenticated,
        created_at=current_user.created_at
    )
