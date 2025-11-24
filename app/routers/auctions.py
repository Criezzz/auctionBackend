"""
Auction management endpoints (UC05 - Register auction, UC08 - View auction details, UC11 - Delete auction)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/auctions", tags=["Auctions"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.Auction)
def register_auction(
    auction: schemas.AuctionCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register new auction (UC05)
    
    POST /auctions/register
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_name": "Figure Auction", "product_id": 1, "start_date": "...", "end_date": "...", "price_step": 10000 }
    Returns: Created auction information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if product exists
    product = crud.get_product(db=db, product_id=auction.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Validate dates
    if auction.start_date >= auction.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    # Create auction
    db_auction = crud.create_auction(db=db, auction=auction)
    
    return schemas.Auction(
        auction_id=db_auction.auction_id,
        auction_name=db_auction.auction_name,
        product_id=db_auction.product_id,
        start_date=db_auction.start_date,
        end_date=db_auction.end_date,
        price_step=db_auction.price_step,
        auction_status=db_auction.auction_status,
        bid_winner_id=db_auction.bid_winner_id,
        created_at=db_auction.created_at,
        updated_at=db_auction.updated_at
    )


@router.get("/", response_model=list[schemas.Auction])
def get_auctions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all auctions
    
    GET /auctions?skip=0&limit=100
    Returns: List of auctions
    """
    auctions = crud.get_auctions(db=db, skip=skip, limit=limit)
    return auctions


@router.get("/{auction_id}", response_model=schemas.AuctionDetail)
def get_auction_details(auction_id: int, db: Session = Depends(get_db)):
    """
    Get auction details (UC08)
    
    GET /auctions/{auction_id}
    Returns: Detailed auction information
    """
    # Get auction with details
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Get product information
    product = crud.get_product(db=db, product_id=auction.product_id)
    
    # Get bids for this auction
    bids = crud.get_bids_by_auction(db=db, auction_id=auction_id)
    
    # Get current highest bid
    current_highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    current_price = current_highest_bid.bid_price if current_highest_bid else None
    
    return schemas.AuctionDetail(
        auction_id=auction.auction_id,
        auction_name=auction.auction_name,
        product_id=auction.product_id,
        start_date=auction.start_date,
        end_date=auction.end_date,
        price_step=auction.price_step,
        auction_status=auction.auction_status,
        bid_winner_id=auction.bid_winner_id,
        created_at=auction.created_at,
        updated_at=auction.updated_at,
        product=schemas.Product(
            product_id=product.product_id,
            product_name=product.product_name,
            product_description=product.product_description,
            product_type=product.product_type,
            shipping_status=product.shipping_status,
            created_at=product.created_at,
            updated_at=product.updated_at
        ) if product else None,
        bids=[schemas.Bid(
            bid_id=bid.bid_id,
            auction_id=bid.auction_id,
            user_id=bid.user_id,
            bid_price=bid.bid_price,
            bid_status=bid.bid_status,
            created_at=bid.created_at
        ) for bid in bids],
        current_price=current_price
    )


@router.put("/{auction_id}", response_model=schemas.Auction)
def update_auction(
    auction_id: int,
    auction_update: schemas.AuctionUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update auction information (Admin only)
    
    PUT /auctions/{auction_id}
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_name": "...", "start_date": "...", ... }
    Returns: Updated auction information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate dates if provided
    if auction_update.start_date and auction_update.end_date:
        if auction_update.start_date >= auction_update.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
    
    # Update auction
    updated_auction = crud.update_auction(db=db, auction_id=auction_id, auction_update=auction_update)
    
    if not updated_auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    return schemas.Auction(
        auction_id=updated_auction.auction_id,
        auction_name=updated_auction.auction_name,
        product_id=updated_auction.product_id,
        start_date=updated_auction.start_date,
        end_date=updated_auction.end_date,
        price_step=updated_auction.price_step,
        auction_status=updated_auction.auction_status,
        bid_winner_id=updated_auction.bid_winner_id,
        created_at=updated_auction.created_at,
        updated_at=updated_auction.updated_at
    )


@router.delete("/{auction_id}", response_model=schemas.MessageResponse)
def delete_auction(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete auction (Admin only - UC11)
    
    DELETE /auctions/{auction_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get auction to check conditions
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction can be deleted (not started, no participants, etc.)
    if auction.auction_status and auction.auction_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete auction that has started or ended"
        )
    
    # Check if there are any bids
    bids = crud.get_bids_by_auction(db=db, auction_id=auction_id)
    if bids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete auction with existing bids"
        )
    
    # Check time restriction (30 minutes before start)
    time_diff = auction.start_date - datetime.utcnow()
    if time_diff.total_seconds() < 1800:  # 30 minutes
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete auction within 30 minutes of start time"
        )
    
    # Delete auction
    success = crud.delete_auction(db=db, auction_id=auction_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    return schemas.MessageResponse(message="Auction deleted successfully")


@router.get("/registered/list", response_model=list[schemas.Auction])
def get_registered_auctions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get auctions with 'registered' status (Admin only)
    
    GET /auctions/registered/list
    Headers: Authorization: Bearer <access_token>
    Returns: List of registered auctions
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all auctions and filter by status
    all_auctions = crud.get_auctions(db=db, skip=0, limit=1000)
    registered_auctions = [a for a in all_auctions if a.auction_status == "registered" or a.auction_status == "pending"]
    
    return registered_auctions