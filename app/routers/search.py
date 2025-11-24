"""
Search and filtering endpoints (UC10 - Search auction information)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/search", tags=["Search"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/auctions", response_model=list[schemas.Auction])
def search_auctions(
    search_params: schemas.AuctionSearch,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search auctions based on criteria (UC10)
    
    POST /search/auctions
    Headers: Authorization: Bearer <access_token>
    Body: { "auction_name": "figure", "auction_status": "active", "product_type": "static", "min_price_step": 10000, "max_price_step": 100000 }
    Returns: List of matching auctions
    """
    # Search auctions
    auctions = crud.search_auctions(db=db, search_params=search_params, skip=skip, limit=limit)
    
    # If product_type filter is provided, we need to filter by joining with products
    if search_params.product_type:
        filtered_auctions = []
        for auction in auctions:
            if auction.product and auction.product.product_type == search_params.product_type:
                filtered_auctions.append(auction)
        auctions = filtered_auctions
    
    return auctions


@router.get("/auctions", response_model=list[schemas.Auction])
def search_auctions_by_query(
    auction_name: str = None,
    auction_status: str = None,
    product_type: str = None,
    min_price_step: int = None,
    max_price_step: int = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search auctions using query parameters (UC10)
    
    GET /search/auctions?auction_name=figure&auction_status=active&product_type=static
    Headers: Authorization: Bearer <access_token>
    Returns: List of matching auctions
    """
    # Build search parameters
    search_params = schemas.AuctionSearch(
        auction_name=auction_name,
        auction_status=auction_status,
        product_type=product_type,
        min_price_step=min_price_step,
        max_price_step=max_price_step
    )
    
    # Search auctions
    auctions = crud.search_auctions(db=db, search_params=search_params, skip=skip, limit=limit)
    
    # If product_type filter is provided, we need to filter by joining with products
    if product_type:
        filtered_auctions = []
        for auction in auctions:
            if auction.product and auction.product.product_type == product_type:
                filtered_auctions.append(auction)
        auctions = filtered_auctions
    
    return auctions


@router.get("/auctions/status/{status}", response_model=list[schemas.Auction])
def get_auctions_by_status(
    status: str,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get auctions by status
    
    GET /search/auctions/status/active
    Headers: Authorization: Bearer <access_token>
    Returns: List of auctions with specified status
    """
    search_params = schemas.AuctionSearch(auction_status=status)
    auctions = crud.search_auctions(db=db, search_params=search_params, skip=skip, limit=limit)
    return auctions


@router.get("/products/type/{product_type}", response_model=list[schemas.Product])
def get_products_by_type(
    product_type: str,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get products by type
    
    GET /search/products/type/static
    Headers: Authorization: Bearer <access_token>
    Returns: List of products with specified type
    """
    all_products = crud.get_products(db=db, skip=skip, limit=limit)
    filtered_products = [p for p in all_products if p.product_type == product_type]
    return filtered_products


@router.get("/auctions/price-range", response_model=list[schemas.Auction])
def get_auctions_by_price_range(
    min_price: int,
    max_price: int,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get auctions within price range
    
    GET /search/auctions/price-range?min_price=10000&max_price=100000
    Headers: Authorization: Bearer <access_token>
    Returns: List of auctions within price range
    """
    search_params = schemas.AuctionSearch(
        min_price_step=min_price,
        max_price_step=max_price
    )
    auctions = crud.search_auctions(db=db, search_params=search_params, skip=skip, limit=limit)
    return auctions


@router.get("/auctions/upcoming", response_model=list[schemas.Auction])
def get_upcoming_auctions(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming auctions
    
    GET /search/auctions/upcoming
    Headers: Authorization: Bearer <access_token>
    Returns: List of upcoming auctions
    """
    from datetime import datetime
    current_time = datetime.utcnow()
    
    all_auctions = crud.get_auctions(db=db, skip=skip, limit=limit)
    upcoming_auctions = [
        auction for auction in all_auctions 
        if auction.start_date > current_time and (auction.auction_status == "pending" or auction.auction_status is None)
    ]
    
    return upcoming_auctions


@router.get("/auctions/active", response_model=list[schemas.Auction])
def get_active_auctions(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get currently active auctions
    
    GET /search/auctions/active
    Headers: Authorization: Bearer <access_token>
    Returns: List of active auctions
    """
    from datetime import datetime
    current_time = datetime.utcnow()
    
    all_auctions = crud.get_auctions(db=db, skip=skip, limit=limit)
    active_auctions = [
        auction for auction in all_auctions 
        if auction.start_date <= current_time <= auction.end_date and auction.auction_status == "active"
    ]
    
    return active_auctions


@router.get("/auctions/ended", response_model=list[schemas.Auction])
def get_ended_auctions(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ended auctions
    
    GET /search/auctions/ended
    Headers: Authorization: Bearer <access_token>
    Returns: List of ended auctions
    """
    from datetime import datetime
    current_time = datetime.utcnow()
    
    all_auctions = crud.get_auctions(db=db, skip=skip, limit=limit)
    ended_auctions = [
        auction for auction in all_auctions 
        if auction.end_date < current_time or auction.auction_status == "ended"
    ]
    
    return ended_auctions