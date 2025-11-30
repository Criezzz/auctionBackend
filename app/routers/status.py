"""
Status management endpoints (UC02 - Update product status, UC03 - Update auction result, UC04 - View product status)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/status", tags=["Status Management"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.put("/product/{product_id}", response_model=schemas.Product)
def update_product_status(
    product_id: int,
    status_update: schemas.ProductStatusUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update product shipping status (UC02 - Admin only)
    
    PUT /status/product/{product_id}
    Headers: Authorization: Bearer <access_token>
    Body: { "shipping_status": "shipped" }
    Returns: Updated product information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Update product status
    product_update = schemas.ProductUpdate(shipping_status=status_update.shipping_status)
    updated_product = crud.update_product(db=db, product_id=product_id, product_update=product_update)
    
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Parse additional_images JSON string back to list
    additional_images_list = None
    if updated_product.additional_images:
        import json
        try:
            additional_images_list = json.loads(updated_product.additional_images)
        except:
            additional_images_list = None
    
    return schemas.Product(
        product_id=updated_product.product_id,
        product_name=updated_product.product_name,
        product_description=updated_product.product_description,
        product_type=updated_product.product_type,
        image_url=updated_product.image_url,
        additional_images=additional_images_list,
        shipping_status=updated_product.shipping_status,
        created_at=updated_product.created_at,
        updated_at=updated_product.updated_at
    )


@router.put("/auction/{auction_id}/result", response_model=schemas.Auction)
def update_auction_result(
    auction_id: int,
    result_update: schemas.AuctionResultUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update auction result (UC03 - Admin only)
    
    PUT /status/auction/{auction_id}/result
    Headers: Authorization: Bearer <access_token>
    Body: { "bid_winner_id": 123 }
    Returns: Updated auction information
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
    
    # Check if auction has ended
    if datetime.utcnow() < auction.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update result before auction ends"
        )
    
    # Check if bid winner exists
    winner = crud.get_account_by_id(db=db, account_id=result_update.bid_winner_id)
    if not winner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid winner not found"
        )
    
    # Update auction result
    auction_update = schemas.AuctionUpdate(
        bid_winner_id=result_update.bid_winner_id,
        auction_status="completed"
    )
    updated_auction = crud.update_auction(db=db, auction_id=auction_id, auction_update=auction_update)
    
    if not updated_auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update auction result"
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


@router.get("/product/{product_id}", response_model=dict)
def get_product_status(
    product_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View product status after auction (UC04)
    
    GET /status/product/{product_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Product status information
    """
    # Get product
    product = crud.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get auctions for this product
    all_auctions = crud.get_auctions(db=db, skip=0, limit=1000)
    product_auctions = [a for a in all_auctions if a.product_id == product_id]
    
    if not product_auctions:
        return {
            "product": {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "shipping_status": product.shipping_status,
                "created_at": product.created_at
            },
            "auction_status": "no_auctions",
            "message": "No auctions found for this product"
        }
    
    # Get the most recent auction
    latest_auction = max(product_auctions, key=lambda x: x.created_at)
    
    # Check user permissions
    can_view_detailed_status = (
        current_user.is_admin or 
        (latest_auction.bid_winner_id == current_user.account_id)
    )
    
    status_info = {
        "product": {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_description": product.product_description,
            "product_type": product.product_type,
            "shipping_status": product.shipping_status,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        },
        "latest_auction": {
            "auction_id": latest_auction.auction_id,
            "auction_name": latest_auction.auction_name,
            "start_date": latest_auction.start_date,
            "end_date": latest_auction.end_date,
            "auction_status": latest_auction.auction_status,
            "bid_winner_id": latest_auction.bid_winner_id,
            "created_at": latest_auction.created_at
        },
        "auction_count": len(product_auctions)
    }
    
    if can_view_detailed_status:
        # Get payment information
        payments = crud.get_payments_by_auction(db=db, auction_id=latest_auction.auction_id)
        
        status_info["detailed_status"] = {
            "payment_status": "no_payment",
            "payment_methods": [],
            "shipping_options": [],
            "receiving_info": {}
        }
        
        if payments:
            payment = payments[0]  # Get first payment
            status_info["detailed_status"]["payment_status"] = payment.payment_status
            status_info["detailed_status"]["payment_method"] = payment.user_payment_method
            status_info["detailed_status"]["receiving_option"] = payment.user_receiving_option
            status_info["detailed_status"]["shipping_address"] = payment.user_address
            
            if payment.user_receiving_option:
                status_info["detailed_status"]["shipping_options"].append(payment.user_receiving_option)
    
    return status_info


@router.get("/auction/{auction_id}/complete", response_model=dict)
def get_auction_completion_status(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive auction completion status (Admin and winner only)
    
    GET /status/auction/{auction_id}/complete
    Headers: Authorization: Bearer <access_token>
    Returns: Comprehensive auction status
    """
    # Get auction
    auction = crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check permissions
    if not current_user.is_admin and auction.bid_winner_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get product information
    product = crud.get_product(db=db, product_id=auction.product_id)
    
    # Get payment information
    payments = crud.get_payments_by_auction(db=db, auction_id=auction_id)
    payment = payments[0] if payments else None
    
    # Get winner information
    winner = None
    if auction.bid_winner_id:
        winner = crud.get_account_by_id(db=db, account_id=auction.bid_winner_id)
    
    # Get highest bid
    highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    
    completion_status = {
        "auction": {
            "auction_id": auction.auction_id,
            "auction_name": auction.auction_name,
            "start_date": auction.start_date,
            "end_date": auction.end_date,
            "final_price": highest_bid.bid_price if highest_bid else None,
            "auction_status": auction.auction_status,
            "completion_date": auction.updated_at
        },
        "product": {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "shipping_status": product.shipping_status
        } if product else None,
        "winner": {
            "user_id": winner.account_id,
            "username": winner.username,
            "first_name": winner.first_name,
            "last_name": winner.last_name,
            "email": winner.email
        } if winner else None,
        "payment": {
            "payment_status": payment.payment_status if payment else "no_payment",
            "payment_method": payment.user_payment_method if payment else None,
            "payment_date": None  # Would be added in real system
        } if payment else None,
        "shipping": {
            "status": product.shipping_status if product else None,
            "estimated_delivery": None,  # Would be calculated in real system
            "tracking_number": None  # Would be added in real system
        }
    }
    
    return completion_status


@router.post("/auction/{auction_id}/finalize", response_model=schemas.MessageResponse)
def finalize_auction(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize auction and update all related statuses (Admin only)
    
    POST /status/auction/{auction_id}/finalize
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
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
    
    # Check if auction has ended
    if datetime.utcnow() < auction.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot finalize auction before it ends"
        )
    
    # Get highest bid
    highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction_id)
    if not highest_bid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No bids found for this auction"
        )
    
    # Update auction with winner
    auction_update = schemas.AuctionUpdate(
        bid_winner_id=highest_bid.user_id,
        auction_status="finalized"
    )
    updated_auction = crud.update_auction(db=db, auction_id=auction_id, auction_update=auction_update)
    
    if not updated_auction:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update auction"
        )
    
    # Update product shipping status to "sold"
    product_update = schemas.ProductUpdate(shipping_status="sold")
    crud.update_product(db=db, product_id=auction.product_id, product_update=product_update)
    
    return schemas.MessageResponse(
        message=f"Auction finalized. Winner: User {highest_bid.user_id}, Final price: {highest_bid.bid_price} VND"
    )