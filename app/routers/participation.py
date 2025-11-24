"""
Auction participation endpoints (UC15 - Register for participation, UC16 - Unregister from participation)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user
from ..utils.qr_token import generate_payment_token, generate_qr_url
from ..utils import mailer

router = APIRouter(prefix="/participation", tags=["Participation"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.MessageResponse)
async def register_for_auction(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register to participate in auction (UC15) - UPDATED with deposit payment
    
    POST /participation/register
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_id": 1 }
    Returns: Success message with payment details
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction is still accepting registrations
    if auction.start_date <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for auction that has already started"
        )
    
    # Check if auction is cancelled or ended
    if auction.auction_status in ["cancelled", "ended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for cancelled or ended auction"
        )
    
    # Check if user already has a deposit payment for this auction
    existing_deposit_payments = db.query(crud.models.Payment).filter(
        crud.models.Payment.auction_id == auction_id,
        crud.models.Payment.user_id == current_user.account_id,
        crud.models.Payment.payment_type == "deposit"
    ).all()
    
    if existing_deposit_payments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already registered for this auction"
        )
    
    # Check participation limits (example: max 50 participants)
    existing_participants = db.query(crud.models.Payment).filter(
        crud.models.Payment.auction_id == auction_id,
        crud.models.Payment.payment_type == "deposit"
    ).count()
    
    if existing_participants >= 50:  # Example limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has reached maximum number of participants"
        )
    
    # Calculate deposit amount
    deposit_amount = auction.price_step * 10  # 10x price step as deposit
    
    # Create deposit payment record
    from .. import models
    
    deposit_payment = models.Payment(
        auction_id=auction_id,
        user_id=current_user.account_id,
        first_name=current_user.first_name or "",
        last_name=current_user.last_name or "",
        user_address="",  # Will be filled later
        user_receiving_option="",
        user_payment_method="bank_transfer",  # Default method
        payment_status="pending",
        payment_type="deposit",
        amount=deposit_amount,
        created_at=datetime.utcnow()
    )
    
    db.add(deposit_payment)
    db.commit()
    db.refresh(deposit_payment)
    
    # Generate payment token for deposit
    token, expires_at = generate_payment_token(
        payment_id=deposit_payment.payment_id,
        user_id=current_user.account_id,
        amount=deposit_amount,
        payment_type="deposit",
        db=db
    )
    
    # Generate QR URL
    qr_url = generate_qr_url(token)
    
    # Send deposit email in background
    asyncio.create_task(
        mailer.send_deposit_email(
            username=current_user.username,
            email=current_user.email,
            auction_name=auction.auction_name,
            deposit_amount=deposit_amount,
            qr_url=qr_url,
            expires_at=expires_at
        )
    )
    
    return schemas.MessageResponse(
        message=f"Successfully registered for auction. Deposit payment created. Payment ID: {deposit_payment.payment_id}. Please check your email for payment instructions."
    )


@router.post("/unregister", response_model=schemas.MessageResponse)
def unregister_from_auction(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unregister from auction participation (UC16)
    
    POST /participation/unregister
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_id": 1 }
    Returns: Success message
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction has started
    if auction.start_date <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unregister after auction has started"
        )
    
    # Check if user has placed any bids
    user_bids = crud.get_bids_by_user(db=db, user_id=current_user.account_id)
    auction_bids = [bid for bid in user_bids if bid.auction_id == auction_id and bid.bid_status == "active"]
    
    if auction_bids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unregister after placing bids"
        )
    
    # Check if user is the current highest bidder in the last 10 minutes
    current_highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    if current_highest_bid and current_highest_bid.user_id == current_user.account_id:
        time_diff = datetime.utcnow() - current_highest_bid.created_at
        if time_diff <= timedelta(minutes=10):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unregister while leading in the last 10 minutes"
            )
    
    # In a real system, you'd:
    # 1. Delete or update the participation record
    # 2. Process refund of deposit
    # 3. Update participant count
    
    return schemas.MessageResponse(
        message="Successfully unregistered from auction. Deposit will be refunded."
    )


@router.get("/my-registrations", response_model=list[dict])
def get_my_registrations(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's auction registrations
    
    GET /participation/my-registrations
    Headers: Authorization: Bearer <access_token>
    Returns: List of user's auction registrations
    """
    # Get all auctions
    all_auctions = crud.get_auctions(db=db, skip=skip, limit=limit)
    
    # Get user's bids to determine participation
    user_bids = crud.get_bids_by_user(db=db, user_id=current_user.account_id, skip=0, limit=1000)
    
    # Filter auctions where user has participated
    registrations = []
    for auction in all_auctions:
        auction_bids = [bid for bid in user_bids if bid.auction_id == auction.auction_id]
        if auction_bids:
            latest_bid = max(auction_bids, key=lambda x: x.created_at)
            registrations.append({
                "auction_id": auction.auction_id,
                "auction_name": auction.auction_name,
                "registration_date": latest_bid.created_at,
                "status": auction.auction_status,
                "is_leading": latest_bid.bid_id == crud.get_current_highest_bid(db=db, auction_id=auction.auction_id).bid_id if crud.get_current_highest_bid(db=db, auction_id=auction.auction_id) else False
            })
    
    return registrations


@router.get("/auction/{auction_id}/participants", response_model=list[dict])
def get_auction_participants(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get participants for an auction (Admin only)
    
    GET /participation/auction/{auction_id}/participants
    Headers: Authorization: Bearer <access_token>
    Returns: List of auction participants
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Get all bids for this auction to determine participants
    bids = crud.get_bids_by_auction(db=db, auction_id=auction_id)
    
    # Get unique participants
    participants = {}
    for bid in bids:
        if bid.user_id not in participants:
            participant = crud.get_account_by_id(db=db, account_id=bid.user_id)
            if participant:
                participants[bid.user_id] = {
                    "user_id": bid.user_id,
                    "username": participant.username,
                    "first_name": participant.first_name,
                    "last_name": participant.last_name,
                    "total_bids": 0,
                    "highest_bid": 0,
                    "latest_bid": None
                }
        
        participants[bid.user_id]["total_bids"] += 1
        if bid.bid_price > participants[bid.user_id]["highest_bid"]:
            participants[bid.user_id]["highest_bid"] = bid.bid_price
        if participants[bid.user_id]["latest_bid"] is None or bid.created_at > participants[bid.user_id]["latest_bid"]:
            participants[bid.user_id]["latest_bid"] = bid.created_at
    
    return list(participants.values())


@router.get("/auction/{auction_id}/status", response_model=dict)
def get_auction_participation_status(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check user's participation status for an auction
    
    GET /participation/auction/{auction_id}/status
    Headers: Authorization: Bearer <access_token>
    Returns: Participation status information
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if user has placed any bids
    user_bids = crud.get_bids_by_user(db=db, user_id=current_user.account_id)
    auction_bids = [bid for bid in user_bids if bid.auction_id == auction_id]
    
    if not auction_bids:
        return {
            "is_registered": False,
            "message": "Not registered for this auction"
        }
    
    # Get current highest bid
    current_highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    is_leading = current_highest_bid and current_highest_bid.user_id == current_user.account_id
    
    latest_bid = max(auction_bids, key=lambda x: x.created_at)
    
    return {
        "is_registered": True,
        "is_leading": is_leading,
        "total_bids": len(auction_bids),
        "highest_bid": max(bid.bid_price for bid in auction_bids),
        "latest_bid": latest_bid.bid_price,
        "registration_date": latest_bid.created_at,
        "auction_status": auction.auction_status
    }