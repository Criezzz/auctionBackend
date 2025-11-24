"""
Account management endpoints (UC06 - Create account)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.UserResponse)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    """
    Create new account (UC06)
    
    POST /accounts/register
    Body: { "username": "user123", "email": "user@example.com", "password": "secret", ... }
    Returns: User account information
    """
    # Check if username already exists
    existing_user = crud.get_account_by_username(db, account.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = db.query(crud.models.Account).filter(
        crud.models.Account.email == account.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create account
    db_account = crud.create_account(db=db, account=account)
    
    return schemas.UserResponse(
        id=db_account.account_id,
        username=db_account.username,
        email=db_account.email,
        role="admin" if db_account.is_admin else "user",
        first_name=db_account.first_name,
        last_name=db_account.last_name,
        phone_num=db_account.phone_num,
        date_of_birth=db_account.date_of_birth,
        activated=db_account.activated,
        is_authenticated=db_account.is_authenticated,
        created_at=db_account.created_at,
        updated_at=db_account.updated_at
    )


@router.get("/profile", response_model=schemas.UserResponse)
def get_user_profile(current_user = Depends(get_current_user)):
    """
    Get current user profile information
    
    GET /accounts/profile
    Headers: Authorization: Bearer <access_token>
    Returns: User profile information
    """
    return schemas.UserResponse(
        id=current_user.account_id,
        username=current_user.username,
        email=current_user.email,
        role="admin" if current_user.is_admin else "user",
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone_num=current_user.phone_num,
        date_of_birth=current_user.date_of_birth,
        activated=current_user.activated,
        is_authenticated=current_user.is_authenticated,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/profile", response_model=schemas.UserResponse)
def update_user_profile(
    profile_update: schemas.AccountUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information (UC007)
    
    PUT /accounts/profile
    Headers: Authorization: Bearer <access_token>
    Body: { "first_name": "John", "last_name": "Doe", ... }
    Returns: Updated user profile
    """
    # Check if email is being updated and if it already exists
    if profile_update.email and profile_update.email != current_user.email:
        existing_email = db.query(crud.models.Account).filter(
            crud.models.Account.email == profile_update.email,
            crud.models.Account.account_id != current_user.account_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update account
    updated_account = crud.update_account(db, current_user.account_id, profile_update)
    
    if not updated_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return schemas.UserResponse(
        id=updated_account.account_id,
        username=updated_account.username,
        email=updated_account.email,
        role="admin" if updated_account.is_admin else "user",
        first_name=updated_account.first_name,
        last_name=updated_account.last_name,
        phone_num=updated_account.phone_num,
        date_of_birth=updated_account.date_of_birth,
        activated=updated_account.activated,
        is_authenticated=updated_account.is_authenticated,
        created_at=updated_account.created_at,
        updated_at=updated_account.updated_at
    )