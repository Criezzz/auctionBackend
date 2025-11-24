"""
Payment management endpoints (UC01 - Update payment status, UC14 - View payment status, UC19 - Make payment)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user
from ..utils.qr_token import verify_payment_token, invalidate_token, get_token_status, generate_payment_token, generate_qr_url
from ..utils import mailer
import asyncio

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/create", response_model=schemas.Payment)
async def create_payment(
    payment: schemas.PaymentCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create payment for won auction (UC19) - UPDATED with QR token generation
    
    POST /payments/create
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_id": 1, "first_name": "John", "last_name": "Doe", "user_address": "...", "user_payment_method": "bank_transfer" }
    Returns: Created payment information
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=payment.auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if user won the auction
    if auction.bid_winner_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only make payment for auctions you won"
        )
    
    # Check if payment already exists
    existing_payments = crud.get_payments_by_auction(db=db, auction_id=payment.auction_id)
    user_payments = [p for p in existing_payments if p.user_id == current_user.account_id]
    
    if user_payments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already exists for this auction"
        )
    
    # Calculate final payment amount (auction winner bid price)
    # In a real system, this would be the final winning bid amount
    final_payment_amount = getattr(auction, 'price_step', 100000) * 100  # Placeholder calculation
    
    # Create payment with payment_type="final_payment"
    db_payment = crud.create_payment(db=db, payment=payment, user_id=current_user.account_id)
    
    # Update the payment with required fields for QR system
    db_payment.payment_type = "final_payment"
    db_payment.amount = final_payment_amount
    db_payment.created_at = datetime.utcnow()
    db.commit()
    db.refresh(db_payment)
    
    # Generate payment token for final payment (24h expiry)
    token, expires_at = generate_payment_token(
        payment_id=db_payment.payment_id,
        user_id=current_user.account_id,
        amount=final_payment_amount,
        payment_type="final_payment",
        db=db
    )
    
    # Generate QR URL
    qr_url = generate_qr_url(token)
    
    # Send payment email in background
    asyncio.create_task(
        mailer.send_payment_email(
            username=current_user.username,
            email=current_user.email,
            auction_name=auction.auction_name,
            final_amount=final_payment_amount,
            qr_url=qr_url,
            expires_at=expires_at
        )
    )
    
    return schemas.Payment(
        payment_id=db_payment.payment_id,
        auction_id=db_payment.auction_id,
        user_id=db_payment.user_id,
        first_name=db_payment.first_name,
        last_name=db_payment.last_name,
        user_address=db_payment.user_address,
        user_receiving_option=db_payment.user_receiving_option,
        user_payment_method=db_payment.user_payment_method,
        payment_status=db_payment.payment_status,
        payment_type=db_payment.payment_type,
        amount=db_payment.amount,
        created_at=db_payment.created_at
    )


@router.put("/{payment_id}/status", response_model=schemas.Payment)
def update_payment_status(
    payment_id: int,
    status_update: schemas.PaymentStatusUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update payment status (UC01 - Admin only) - UPDATED with token invalidation
    
    PUT /payments/{payment_id}/status
    Headers: Authorization: Bearer <access_token>
    Body: { "payment_status": "completed" }
    Returns: Updated payment information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get payment before updating
    payment = crud.get_payment(db=db, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Update payment status
    updated_payment = crud.update_payment_status(db=db, payment_id=payment_id, status=status_update.payment_status)
    
    # If marking as completed, invalidate any associated tokens
    if status_update.payment_status == "completed":
        # Find and invalidate any active tokens for this payment
        tokens = db.query(crud.models.PaymentToken).filter(
            crud.models.PaymentToken.payment_id == payment_id,
            crud.models.PaymentToken.is_used == False
        ).all()
        
        for token in tokens:
            invalidate_token(token.token, db)
    
    return schemas.Payment(
        payment_id=updated_payment.payment_id,
        auction_id=updated_payment.auction_id,
        user_id=updated_payment.user_id,
        first_name=updated_payment.first_name,
        last_name=updated_payment.last_name,
        user_address=updated_payment.user_address,
        user_receiving_option=updated_payment.user_receiving_option,
        user_payment_method=updated_payment.user_payment_method,
        payment_status=updated_payment.payment_status,
        payment_type=getattr(updated_payment, 'payment_type', 'final_payment'),
        amount=getattr(updated_payment, 'amount', 0),
        created_at=getattr(updated_payment, 'created_at', datetime.utcnow())
    )


@router.get("/my-payments", response_model=list[schemas.Payment])
def get_my_payments(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's payments
    
    GET /payments/my-payments
    Headers: Authorization: Bearer <access_token>
    Returns: List of user's payments
    """
    payments = crud.get_payments_by_user(db=db, user_id=current_user.account_id, skip=skip, limit=limit)
    return payments


@router.get("/auction/{auction_id}", response_model=schemas.Payment)
def get_auction_payment(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment for specific auction (UC14)
    
    GET /payments/auction/{auction_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Payment information
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if user has permission to view payment
    if not current_user.is_admin and auction.bid_winner_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view payments for auctions you won"
        )
    
    # Get payment
    payments = crud.get_payments_by_auction(db=db, auction_id=auction_id)
    payment = None
    
    if current_user.is_admin:
        payment = payments[0] if payments else None
    else:
        payment = next((p for p in payments if p.user_id == current_user.account_id), None)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return schemas.Payment(
        payment_id=payment.payment_id,
        auction_id=payment.auction_id,
        user_id=payment.user_id,
        first_name=payment.first_name,
        last_name=payment.last_name,
        user_address=payment.user_address,
        user_receiving_option=payment.user_receiving_option,
        user_payment_method=payment.user_payment_method,
        payment_status=payment.payment_status,
        payment_type=getattr(payment, 'payment_type', 'final_payment'),
        amount=getattr(payment, 'amount', 0),
        created_at=getattr(payment, 'created_at', datetime.utcnow())
    )


@router.get("/{payment_id}", response_model=schemas.Payment)
def get_payment(
    payment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment by ID
    
    GET /payments/{payment_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Payment information
    """
    # Get payment
    payment = crud.get_payment(db=db, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if user has permission to view payment
    if not current_user.is_admin and payment.user_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own payments"
        )
    
    return schemas.Payment(
        payment_id=payment.payment_id,
        auction_id=payment.auction_id,
        user_id=payment.user_id,
        first_name=payment.first_name,
        last_name=payment.last_name,
        user_address=payment.user_address,
        user_receiving_option=payment.user_receiving_option,
        user_payment_method=payment.user_payment_method,
        payment_status=payment.payment_status,
        payment_type=getattr(payment, 'payment_type', 'final_payment'),
        amount=getattr(payment, 'amount', 0),
        created_at=getattr(payment, 'created_at', datetime.utcnow())
    )


@router.get("/all/pending", response_model=list[schemas.Payment])
def get_pending_payments(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending payments (Admin only)
    
    GET /payments/all/pending
    Headers: Authorization: Bearer <access_token>
    Returns: List of pending payments
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all payments and filter by status
    from sqlalchemy import and_
    pending_payments = db.query(crud.models.Payment).filter(
        and_(
            crud.models.Payment.payment_status == "pending"
        )
    ).all()
    
    return pending_payments


@router.post("/{payment_id}/process", response_model=schemas.MessageResponse)
async def process_payment(
    payment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process payment (simulate payment processing - UC19) - UPDATED with token invalidation
    
    POST /payments/{payment_id}/process
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # Get payment
    payment = crud.get_payment(db=db, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if user owns the payment or is admin
    if not current_user.is_admin and payment.user_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only process your own payments"
        )
    
    # Check payment status
    if payment.payment_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has already been processed"
        )
    
    # Invalidate any active tokens for this payment
    tokens = db.query(crud.models.PaymentToken).filter(
        crud.models.PaymentToken.payment_id == payment_id,
        crud.models.PaymentToken.is_used == False
    ).all()
    
    for token in tokens:
        invalidate_token(token.token, db)
    
    # Update payment status to "completed" directly (in real system, this would be async)
    updated_payment = crud.update_payment_status(db=db, payment_id=payment_id, status="completed")
    
    # Get user and auction info for email
    user = db.query(crud.models.Account).filter(
        crud.models.Account.account_id == payment.user_id
    ).first()
    
    auction = db.query(crud.models.Auction).filter(
        crud.models.Auction.auction_id == payment.auction_id
    ).first()
    
    # Send confirmation email
    if user and auction:
        await mailer.send_payment_confirmation_email(
            username=user.username,
            email=user.email,
            auction_name=auction.auction_name,
            payment_amount=payment.amount,
            payment_type=payment.payment_type,
            payment_method="Web Payment"
        )
    
    return schemas.MessageResponse(message="Payment processed successfully")


@router.get("/status/{status}", response_model=list[schemas.Payment])
def get_payments_by_status(
    status: str,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payments by status (Admin only)
    
    GET /payments/status/completed
    Headers: Authorization: Bearer <access_token>
    Returns: List of payments with specified status
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from sqlalchemy import and_
    payments = db.query(crud.models.Payment).filter(
        and_(
            crud.models.Payment.payment_status == status
        )
    ).offset(skip).limit(limit).all()
    
    return payments


# NEW QR PAYMENT ENDPOINTS

@router.post("/qr-callback/{token}")
async def qr_payment_callback(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Mock callback endpoint when QR code is scanned
    This simulates a payment gateway callback
    
    POST /payments/qr-callback/{token}
    Returns: Payment success message or error
    """
    try:
        # Verify and get token data
        token_data = verify_payment_token(token, db)
        
        payment = token_data["payment"]
        
        # Check if payment is already completed
        if payment.payment_status == "completed":
            return {
                "success": False,
                "message": "Payment has already been completed",
                "payment_id": payment.payment_id
            }
        
        # Invalidate the token (mark as used)
        invalidate_token(token, db)
        
        # Update payment status to completed
        updated_payment = crud.update_payment_status(db=db, payment_id=payment.payment_id, status="completed")
        
        # Get user and auction info for email
        user = db.query(crud.models.Account).filter(
            crud.models.Account.account_id == payment.user_id
        ).first()
        
        auction = db.query(crud.models.Auction).filter(
            crud.models.Auction.auction_id == payment.auction_id
        ).first()
        
        # Send confirmation email
        if user and auction:
            await mailer.send_payment_confirmation_email(
                username=user.username,
                email=user.email,
                auction_name=auction.auction_name,
                payment_amount=payment.amount,
                payment_type=payment.payment_type,
                payment_method="QR Code"
            )
        
        return {
            "success": True,
            "message": "Payment completed successfully",
            "payment_id": payment.payment_id,
            "payment_status": "completed",
            "amount": payment.amount,
            "auction_name": auction.auction_name if auction else "Unknown",
            "payment_type": payment.payment_type
        }
        
    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Payment processing error: {str(e)}",
            "status_code": 500
        }


@router.get("/token/{token}/status")
async def get_token_status_endpoint(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get token status information
    
    GET /payments/token/{token}/status
    Returns: Token status details
    """
    status_info = get_token_status(token, db)
    return status_info