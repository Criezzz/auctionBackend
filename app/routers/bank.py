"""
Mock Bank API endpoints
Handles deposits and payments with QR code functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user
from ..bank_port import BankPort

router = APIRouter(prefix="/bank", tags=["Mock Bank API"])

# Initialize bank port
bank_port = BankPort()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =================== DEPOSIT ENDPOINTS (Đặt cọc) =================== #

@router.post("/deposit/create")
def create_deposit(
    auction_id: int = Query(..., description="Auction ID for deposit"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create deposit for auction participation (đặt cọc)
    
    This endpoint is called when user wants to participate in an auction.
    For demo: always returns successful deposit immediately.
    
    GET /bank/deposit/create?auction_id=1
    Headers: Authorization: Bearer <access_token>
    Returns: Deposit transaction with QR code
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Calculate deposit amount
    deposit_amount = bank_port.calculate_deposit_amount(auction)
    
    # Create deposit transaction
    deposit_result = bank_port.create_deposit_transaction(
        db=db,
        user_id=current_user.account_id,
        auction_id=auction_id,
        amount=deposit_amount
    )
    
    return {
        "success": True,
        "message": "Deposit created successfully",
        "data": {
            "transaction_id": deposit_result["transaction_id"],
            "auction_id": auction_id,
            "amount": deposit_amount,
            "status": deposit_result["status"],
            "qr_code": deposit_result["qr_code"],
            "bank_info": {
                "bank_name": bank_port.bank_name,
                "bank_code": bank_port.bank_code
            },
            "created_at": deposit_result["created_at"]
        }
    }


@router.get("/deposit/status/{transaction_id}")
def get_deposit_status(
    transaction_id: str,
    current_user = Depends(get_current_user)
):
    """
    Check deposit transaction status
    
    GET /bank/deposit/status/DEP_ABC123DEF456
    Headers: Authorization: Bearer <access_token>
    Returns: Deposit status
    """
    status_result = bank_port.get_transaction_status(transaction_id)
    
    return {
        "success": True,
        "data": {
            "transaction_id": transaction_id,
            "status": status_result["status"],
            "bank_response": status_result["bank_response"]
        }
    }


# =================== PAYMENT ENDPOINTS (Thanh toán) =================== #

@router.post("/payment/create")
def create_payment(
    payment_request: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create payment for won auction (thanh toán)
    
    This endpoint is called when user wants to pay for a won auction.
    Returns QR code for payment confirmation.
    
    POST /bank/payment/create
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_id": 1, "payment_id": 123 }
    Returns: Payment transaction with QR code
    """
    auction_id = payment_request.get("auction_id")
    payment_id = payment_request.get("payment_id")
    
    if not auction_id or not payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="auction_id and payment_id are required"
        )
    
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
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
    
    # Get payment
    payment = crud.get_payment(db=db, payment_id=payment_id)
    if not payment or payment.user_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Get payment amount
    payment_amount = bank_port.get_payment_amount(db=db, auction=auction)
    
    # Create payment transaction
    payment_result = bank_port.create_payment_transaction(
        db=db,
        user_id=current_user.account_id,
        auction_id=auction_id,
        amount=payment_amount,
        payment_id=payment_id
    )
    
    return {
        "success": True,
        "message": "Payment created - scan QR code to confirm",
        "data": {
            "transaction_id": payment_result["transaction_id"],
            "payment_id": payment_id,
            "auction_id": auction_id,
            "amount": payment_amount,
            "status": payment_result["status"],
            "qr_code": payment_result["qr_code"],
            "bank_info": {
                "bank_name": bank_port.bank_name,
                "bank_code": bank_port.bank_code
            },
            "payment_instructions": "Scan QR code with banking app or click payment link to complete payment",
            "created_at": payment_result["created_at"]
        }
    }


@router.post("/payment/confirm")
def confirm_payment(
    confirmation_data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm payment after QR scan or link click (thanh toán)
    
    This endpoint simulates user confirming payment via QR scan or web link.
    For demo: always returns successful payment.
    
    POST /bank/payment/confirm
    Headers: Authorization: Bearer <access_token>
    Body: { "transaction_id": "PAY_ABC123", "payment_id": 123 }
    Returns: Payment confirmation result
    """
    transaction_id = confirmation_data.get("transaction_id")
    payment_id = confirmation_data.get("payment_id")
    
    if not transaction_id or not payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="transaction_id and payment_id are required"
        )
    
    # Process payment confirmation
    confirmation_result = bank_port.process_payment_confirmation(
        db=db,
        transaction_id=transaction_id,
        payment_id=payment_id
    )
    
    # Update payment status in database if confirmation is successful
    if confirmation_result["status"] == "completed":
        crud.update_payment_status(db=db, payment_id=payment_id, status="completed")
    
    return {
        "success": True,
        "message": "Payment confirmed successfully",
        "data": {
            "transaction_id": confirmation_result["transaction_id"],
            "payment_id": confirmation_result["payment_id"],
            "status": confirmation_result["status"],
            "bank_response": confirmation_result["bank_response"],
            "confirmed_at": confirmation_result["confirmed_at"]
        }
    }


@router.get("/payment/qr/{transaction_id}")
def get_payment_qr(
    transaction_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get QR code for existing payment transaction
    
    GET /bank/payment/qr/PAY_ABC123DEF456
    Headers: Authorization: Bearer <access_token>
    Returns: QR code for payment
    """
    # For demo, generate QR code for the transaction
    qr_code = bank_port.generate_qr_code(
        transaction_id=transaction_id,
        amount=0,  # Amount would be stored elsewhere in real implementation
        description="Auction payment"
    )
    
    return {
        "success": True,
        "data": {
            "transaction_id": transaction_id,
            "qr_code": qr_code,
            "bank_info": {
                "bank_name": bank_port.bank_name,
                "bank_code": bank_port.bank_code
            },
            "payment_instructions": "Scan QR code with your banking app to complete payment"
        }
    }


@router.get("/payment/status/{transaction_id}")
def get_payment_status(
    transaction_id: str,
    current_user = Depends(get_current_user)
):
    """
    Check payment transaction status
    
    GET /bank/payment/status/PAY_ABC123DEF456
    Headers: Authorization: Bearer <access_token>
    Returns: Payment status
    """
    status_result = bank_port.get_transaction_status(transaction_id)
    
    return {
        "success": True,
        "data": {
            "transaction_id": transaction_id,
            "status": status_result["status"],
            "bank_response": status_result["bank_response"]
        }
    }


# =================== TERMS AND CONDITIONS ENDPOINT =================== #

@router.get("/terms")
def get_terms_and_conditions():
    """
    Get terms and conditions for the auction platform
    
    GET /bank/terms
    Returns: Terms and conditions text
    """
    terms_text = """Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7
Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7
Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7
Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7
Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7
Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7
Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7"""
    
    return {
        "success": True,
        "data": {
            "title": "Điều khoản sử dụng",
            "content": terms_text,
            "version": "1.0.0",
            "last_updated": "2025-11-19T09:24:30.000Z"
        }
    }


# =================== UTILITY ENDPOINTS =================== #

@router.get("/banks")
def get_supported_banks():
    """
    Get list of supported banks (mock data)
    
    GET /bank/banks
    Returns: List of supported banks
    """
    banks = [
        {
            "bank_code": bank_port.bank_code,
            "bank_name": bank_port.bank_name,
            "status": "active",
            "qr_support": True
        },
        {
            "bank_code": "VCB",
            "bank_name": "Vietcombank",
            "status": "active",
            "qr_support": True
        },
        {
            "bank_code": "TCB",
            "bank_name": "Techcombank",
            "status": "active",
            "qr_support": True
        },
        {
            "bank_code": "CTG",
            "bank_name": "VietinBank",
            "status": "active",
            "qr_support": True
        }
    ]
    
    return {
        "success": True,
        "data": banks
    }


@router.get("/health")
def bank_health_check():
    """
    Health check endpoint for bank API
    
    GET /bank/health
    Returns: Bank API status
    """
    return {
        "success": True,
        "message": "Mock Bank API is running",
        "data": {
            "bank_name": bank_port.bank_name,
            "bank_code": bank_port.bank_code,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    }