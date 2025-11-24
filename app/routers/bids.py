"""
Bidding endpoints (UC17 - Place bid, UC18 - Cancel bid)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/bids", tags=["Bidding"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/place", response_model=schemas.Bid)
def place_bid(
    bid: schemas.BidCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Place a bid (UC17) - UPDATED with deposit verification
    
    POST /bids/place
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_id": 1, "bid_price": 50000 }
    Returns: Created bid information
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=bid.auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction is active
    current_time = datetime.utcnow()
    if not (auction.start_date <= current_time <= auction.end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not currently active"
        )
    
    if auction.auction_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not accepting bids"
        )
    
    # Verify user has paid deposit for this auction
    deposit_payment = db.query(crud.models.Payment).filter(
        crud.models.Payment.auction_id == bid.auction_id,
        crud.models.Payment.user_id == current_user.account_id,
        crud.models.Payment.payment_type == "deposit",
        crud.models.Payment.payment_status == "completed"
    ).first()
    
    if not deposit_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must register and pay the deposit before placing bids. Please register for participation first."
        )
    
    # Get current highest bid before placing new bid
    previous_highest_bid = crud.get_current_highest_bid(db=db, auction_id=bid.auction_id)
    min_bid_amount = auction.price_step  # Default minimum
    
    if previous_highest_bid:
        min_bid_amount = previous_highest_bid.bid_price + auction.price_step
    
    # Validate bid amount
    if bid.bid_price < min_bid_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid must be at least {min_bid_amount} VND"
        )
    
    # Create bid
    db_bid = crud.create_bid(db=db, bid=bid, user_id=current_user.account_id)
    
    # Check if bid is placed in the last 5 minutes (auto-extend)
    extended = False
    if auction.end_date - current_time <= timedelta(minutes=5):
        # Extend auction by 5 minutes
        auction_update = schemas.AuctionUpdate(
            end_date=auction.end_date + timedelta(minutes=5)
        )
        updated_auction = crud.update_auction(db=db, auction_id=bid.auction_id, auction_update=auction_update)
        extended = True
    
    # Send real-time notifications
    try:
        # Get all bids for this auction to determine participants
        all_bids = crud.get_bids_by_auction(db=db, auction_id=bid.auction_id)
        participant_user_ids = set(bid.user_id for bid in all_bids)
        
        # Get updated highest bid info
        new_highest_bid = crud.get_current_highest_bid(db=db, auction_id=bid.auction_id)
        highest_bidder = crud.get_account_by_id(db=db, account_id=new_highest_bid.user_id) if new_highest_bid else None
        
        # Prepare bid update message
        bid_update_message = {
            "type": "bid_update",
            "data": {
                "auction_id": bid.auction_id,
                "auction_name": auction.auction_name,
                "new_highest_bid": new_highest_bid.bid_price if new_highest_bid else bid.bid_price,
                "new_highest_bidder": {
                    "user_id": highest_bidder.account_id if highest_bidder else current_user.account_id,
                    "username": highest_bidder.username if highest_bidder else current_user.username,
                    "name": f"{highest_bidder.first_name} {highest_bidder.last_name}".strip() if highest_bidder else f"{current_user.first_name} {current_user.last_name}".strip()
                },
                "total_bids": len(all_bids),
                "extended": extended,
                "new_end_time": updated_auction.end_date.isoformat() if extended else auction.end_date.isoformat(),
                "bid_timestamp": db_bid.created_at.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all participants
        asyncio.create_task(crud.broadcast_to_auction_participants(db, bid.auction_id, bid_update_message))
        
        # If someone was outbid, send specific notification
        if previous_highest_bid and previous_highest_bid.user_id != current_user.account_id:
            outbid_notification = schemas.NotificationCreate(
                user_id=previous_highest_bid.user_id,
                auction_id=bid.auction_id,
                notification_type="bid_outbid",
                title="You have been outbid!",
                message=f"{current_user.first_name or current_user.username} placed a higher bid of {bid.bid_price:,} VND on {auction.auction_name}"
            )
            
            # Create notification
            notification = crud.create_notification(db, outbid_notification)
            
            # Send WebSocket notification to outbid user
            if notification:
                outbid_websocket_message = {
                    "type": "bid_outbid",
                    "data": {
                        "notification_id": notification.notification_id,
                        "auction_id": bid.auction_id,
                        "auction_name": auction.auction_name,
                        "previous_bid": previous_highest_bid.bid_price,
                        "new_bid": bid.bid_price,
                        "outbidder_name": f"{current_user.first_name} {current_user.last_name}".strip(),
                        "timestamp": notification.created_at.isoformat()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                asyncio.create_task(crud.send_to_user(previous_highest_bid.user_id, outbid_websocket_message))
        
        # Send confirmation to bidder
        bidder_message = {
            "type": "bid_placed",
            "data": {
                "bid_id": db_bid.bid_id,
                "auction_id": bid.auction_id,
                "bid_amount": bid.bid_price,
                "is_highest": True,  # Since we just placed it
                "message": "Your bid has been placed successfully"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        asyncio.create_task(crud.send_to_user(current_user.account_id, bidder_message))
        
    except Exception as e:
        print(f"Error sending notifications: {e}")
        # Don't fail the bid placement if notifications fail
    
    return schemas.Bid(
        bid_id=db_bid.bid_id,
        auction_id=db_bid.auction_id,
        user_id=db_bid.user_id,
        bid_price=db_bid.bid_price,
        bid_status=db_bid.bid_status,
        created_at=db_bid.created_at
    )


@router.post("/cancel/{bid_id}", response_model=schemas.MessageResponse)
def cancel_bid(
    bid_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a bid (UC18)
    
    POST /bids/cancel/{bid_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # Get bid
    bid = crud.get_bid(db=db, bid_id=bid_id)
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid not found"
        )
    
    # Check if user owns the bid
    if bid.user_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own bids"
        )
    
    # Check if bid is still active
    if bid.bid_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bid is not active"
        )
    
    # Get auction
    auction = crud.get_auction(db=db, auction_id=bid.auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check auction time
    current_time = datetime.utcnow()
    time_diff = auction.end_date - current_time
    
    # Cannot cancel if auction has ended
    if time_diff.total_seconds() <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel bid after auction has ended"
        )
    
    # Cannot cancel if user is leading in the last 10 minutes
    current_highest_bid = crud.get_current_highest_bid(db=db, auction_id=bid.auction_id)
    if current_highest_bid and current_highest_bid.user_id == current_user.account_id:
        if time_diff <= timedelta(minutes=10):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel bid while leading in the last 10 minutes"
            )
        
        # If leading and more than 10 minutes left, allow cancellation but extend auction
        if time_diff > timedelta(minutes=10):
            auction_update = schemas.AuctionUpdate(
                end_date=auction.end_date + timedelta(minutes=5)
            )
            crud.update_auction(db=db, auction_id=bid.auction_id, auction_update=auction_update)
    
    # Cancel bid
    success = crud.cancel_bid(db=db, bid_id=bid_id, user_id=current_user.account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel bid"
        )
    
    return schemas.MessageResponse(message="Bid cancelled successfully")


@router.get("/my-bids", response_model=list[schemas.Bid])
def get_my_bids(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's bid history
    
    GET /bids/my-bids
    Headers: Authorization: Bearer <access_token>
    Returns: List of user's bids
    """
    bids = crud.get_bids_by_user(db=db, user_id=current_user.account_id, skip=skip, limit=limit)
    return bids


@router.get("/auction/{auction_id}", response_model=list[schemas.Bid])
def get_auction_bids(
    auction_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all bids for an auction
    
    GET /bids/auction/{auction_id}
    Headers: Authorization: Bearer <access_token>
    Returns: List of bids for the auction
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    bids = crud.get_bids_by_auction(db=db, auction_id=auction_id, skip=skip, limit=limit)
    return bids


@router.get("/auction/{auction_id}/highest", response_model=schemas.Bid)
def get_highest_bid(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current highest bid for an auction
    
    GET /bids/auction/{auction_id}/highest
    Headers: Authorization: Bearer <access_token>
    Returns: Current highest bid
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    current_highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    if not current_highest_bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bids found for this auction"
        )
    
    return schemas.Bid(
        bid_id=current_highest_bid.bid_id,
        auction_id=current_highest_bid.auction_id,
        user_id=current_highest_bid.user_id,
        bid_price=current_highest_bid.bid_price,
        bid_status=current_highest_bid.bid_status,
        created_at=current_highest_bid.created_at
    )


@router.post("/auction/{auction_id}/my-status", response_model=dict)
def get_my_bid_status(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's bid status for an auction
    
    POST /bids/auction/{auction_id}/my-status
    Headers: Authorization: Bearer <access_token>
    Returns: User's bid status information
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Get user's bids for this auction
    user_bids = crud.get_bids_by_user(db=db, user_id=current_user.account_id)
    auction_bids = [bid for bid in user_bids if bid.auction_id == auction_id]
    
    if not auction_bids:
        return {
            "has_bids": False,
            "message": "You have not placed any bids for this auction"
        }
    
    # Get current highest bid
    current_highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    is_leading = current_highest_bid and current_highest_bid.user_id == current_user.account_id
    
    highest_bid = max(bid.bid_price for bid in auction_bids)
    latest_bid = max(bid.created_at for bid in auction_bids)
    
    return {
        "has_bids": True,
        "is_leading": is_leading,
        "total_bids": len(auction_bids),
        "highest_bid": highest_bid,
        "latest_bid": latest_bid,
        "auction_status": auction.auction_status,
        "time_remaining": (auction.end_date - datetime.utcnow()).total_seconds() if auction.end_date > datetime.utcnow() else 0
    }