from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from . import models, schemas
from .auth import get_password_hash, verify_password


# ========== ITEM CRUD ========== #
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(title=item.title, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# ========== ACCOUNT CRUD ========== #
def get_account_by_username(db: Session, username: str) -> models.Account | None:
    """Get account by username"""
    return db.query(models.Account).filter(models.Account.username == username).first()


def get_account_by_id(db: Session, account_id: int) -> models.Account | None:
    """Get account by ID"""
    return db.query(models.Account).filter(models.Account.account_id == account_id).first()


def create_account(db: Session, account: schemas.AccountCreate) -> models.Account:
    """Create new account with hashed password"""
    hashed_password = get_password_hash(account.password)
    db_account = models.Account(
        username=account.username,
        email=account.email,
        password=hashed_password,
        first_name=account.first_name,
        last_name=account.last_name,
        phone_num=account.phone_num,
        date_of_birth=account.date_of_birth,
        created_at=datetime.utcnow(),
        activated=True,  # Auto-activate for demo; in production, send email verification
        is_admin=False,
        is_authenticated=False
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def authenticate_account(db: Session, username: str, password: str) -> models.Account | None:
    """Authenticate account with username and password"""
    account = get_account_by_username(db, username)
    if not account:
        return None
    if not verify_password(password, account.password):
        return None
    return account


def update_account(db: Session, account_id: int, account_update: schemas.AccountUpdate) -> models.Account | None:
    """Update account information"""
    db_account = get_account_by_id(db, account_id)
    if not db_account:
        return None
    
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db_account.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_unactivated_account(db: Session, username: str) -> bool:
    """Delete unactivated account by username"""
    db_account = get_account_by_username(db, username)
    if not db_account:
        return False
    
    # Can only delete unactivated accounts
    if db_account.activated:
        return False
    
    # Delete the account
    db.delete(db_account)
    db.commit()
    return True


# ========== PRODUCT CRUD ========== #
def get_product(db: Session, product_id: int) -> models.Product | None:
    """Get product by ID"""
    return db.query(models.Product).filter(models.Product.product_id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]:
    """Get all products with pagination"""
    return db.query(models.Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate, user_id: int = None) -> models.Product:
    """Create new product"""
    db_product = models.Product(
        product_name=product.product_name,
        product_description=product.product_description,
        product_type=product.product_type,
        approval_status="pending",
        suggested_by_user_id=user_id,
        created_at=datetime.utcnow()
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> models.Product | None:
    """Update product information"""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db_product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    """Delete product"""
    db_product = get_product(db, product_id)
    if not db_product:
        return False
    
    db.delete(db_product)
    db.commit()
    return True


# ========== AUCTION CRUD ========== #
def get_auction(db: Session, auction_id: int) -> models.Auction | None:
    """Get auction by ID"""
    return db.query(models.Auction).filter(models.Auction.auction_id == auction_id).first()


def get_auctions(db: Session, skip: int = 0, limit: int = 100) -> List[models.Auction]:
    """Get all auctions with pagination"""
    return db.query(models.Auction).offset(skip).limit(limit).all()


def create_auction(db: Session, auction: schemas.AuctionCreate) -> models.Auction:
    """Create new auction"""
    db_auction = models.Auction(
        auction_name=auction.auction_name,
        product_id=auction.product_id,
        start_date=auction.start_date,
        end_date=auction.end_date,
        price_step=auction.price_step,
        created_at=datetime.utcnow(),
        auction_status="pending"
    )
    db.add(db_auction)
    db.commit()
    db.refresh(db_auction)
    return db_auction


def update_auction(db: Session, auction_id: int, auction_update: schemas.AuctionUpdate) -> models.Auction | None:
    """Update auction information"""
    db_auction = get_auction(db, auction_id)
    if not db_auction:
        return None
    
    update_data = auction_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_auction, field, value)
    
    db_auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_auction)
    return db_auction


def delete_auction(db: Session, auction_id: int) -> bool:
    """Delete auction"""
    db_auction = get_auction(db, auction_id)
    if not db_auction:
        return False
    
    db.delete(db_auction)
    db.commit()
    return True


def search_auctions(db: Session, search_params: schemas.AuctionSearch, skip: int = 0, limit: int = 100) -> List[models.Auction]:
    """Search auctions based on criteria"""
    query = db.query(models.Auction)
    
    if search_params.auction_name:
        query = query.filter(models.Auction.auction_name.contains(search_params.auction_name))
    
    if search_params.auction_status:
        query = query.filter(models.Auction.auction_status == search_params.auction_status)
    
    if search_params.min_price_step:
        query = query.filter(models.Auction.price_step >= search_params.min_price_step)
    
    if search_params.max_price_step:
        query = query.filter(models.Auction.price_step <= search_params.max_price_step)
    
    return query.offset(skip).limit(limit).all()


# ========== BID CRUD ========== #
def get_bid(db: Session, bid_id: int) -> models.Bid | None:
    """Get bid by ID"""
    return db.query(models.Bid).filter(models.Bid.bid_id == bid_id).first()


def get_bids_by_auction(db: Session, auction_id: int, skip: int = 0, limit: int = 100) -> List[models.Bid]:
    """Get all bids for an auction"""
    return db.query(models.Bid).filter(models.Bid.auction_id == auction_id).order_by(models.Bid.bid_price.desc()).offset(skip).limit(limit).all()


def get_bids_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Bid]:
    """Get all bids by a user"""
    return db.query(models.Bid).filter(models.Bid.user_id == user_id).offset(skip).limit(limit).all()


def create_bid(db: Session, bid: schemas.BidCreate, user_id: int) -> models.Bid:
    """Create new bid"""
    db_bid = models.Bid(
        auction_id=bid.auction_id,
        user_id=user_id,
        bid_price=bid.bid_price,
        bid_status="active",
        created_at=datetime.utcnow()
    )
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    return db_bid


def cancel_bid(db: Session, bid_id: int, user_id: int) -> bool:
    """Cancel a bid"""
    db_bid = get_bid(db, bid_id)
    if not db_bid or db_bid.user_id != user_id:
        return False
    
    db_bid.bid_status = "cancelled"
    db.commit()
    return True


# ========== PAYMENT CRUD ========== #
def get_payment(db: Session, payment_id: int) -> models.Payment | None:
    """Get payment by ID"""
    return db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()


def get_payments_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Payment]:
    """Get all payments by a user"""
    return db.query(models.Payment).filter(models.Payment.user_id == user_id).offset(skip).limit(limit).all()


def get_payments_by_auction(db: Session, auction_id: int) -> List[models.Payment]:
    """Get all payments for an auction"""
    return db.query(models.Payment).filter(models.Payment.auction_id == auction_id).all()


def create_payment(db: Session, payment: schemas.PaymentCreate, user_id: int) -> models.Payment:
    """Create new payment"""
    db_payment = models.Payment(
        auction_id=payment.auction_id,
        user_id=user_id,
        first_name=payment.first_name,
        last_name=payment.last_name,
        user_address=payment.user_address,
        user_receiving_option=payment.user_receiving_option,
        user_payment_method=payment.user_payment_method,
        payment_status="pending"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def update_payment_status(db: Session, payment_id: int, status: str) -> models.Payment | None:
    """Update payment status"""
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        return None
    
    db_payment.payment_status = status
    db.commit()
    db.refresh(db_payment)
    return db_payment


# ========== UTILITY FUNCTIONS ========== #

def get_auction_with_details(db: Session, auction_id: int) -> models.Auction | None:
    """Get auction with product and bid details"""
    return db.query(models.Auction).filter(models.Auction.auction_id == auction_id).first()


def get_current_highest_bid(db: Session, auction_id: int) -> models.Bid | None:
    """Get the current highest bid for an auction"""
    return db.query(models.Bid).filter(
        models.Bid.auction_id == auction_id,
        models.Bid.bid_status == "active"
    ).order_by(models.Bid.bid_price.desc()).first()


def get_user_won_auctions(db: Session, user_id: int) -> List[models.Auction]:
    """Get auctions won by a user"""
    return db.query(models.Auction).filter(models.Auction.bid_winner_id == user_id).all()


# ========== NOTIFICATION CRUD ========== #
def get_notification(db: Session, notification_id: int) -> models.Notification | None:
    """Get notification by ID"""
    return db.query(models.Notification).filter(models.Notification.notification_id == notification_id).first()


def get_notifications_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Notification]:
    """Get all notifications for a user"""
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id
    ).order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def get_unread_notifications_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Notification]:
    """Get unread notifications for a user"""
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def create_notification(db: Session, notification: schemas.NotificationCreate) -> models.Notification:
    """Create new notification"""
    db_notification = models.Notification(
        user_id=notification.user_id,
        auction_id=notification.auction_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        is_read=False,
        is_sent=False,
        created_at=datetime.utcnow()
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def create_outbid_notification(db: Session, auction_id: int, outbid_user_id: int, new_bidder_id: int, new_bid_price: int) -> models.Notification:
    """Create notification when user is outbid"""
    # Get auction and user information
    auction = get_auction(db, auction_id)
    new_bidder = get_account_by_id(db, new_bidder_id)
    
    if not auction or not new_bidder:
        return None
    
    db_notification = models.Notification(
        user_id=outbid_user_id,
        auction_id=auction_id,
        notification_type="bid_outbid",
        title="You have been outbid!",
        message=f"{new_bidder.first_name or new_bidder.username} placed a higher bid of {new_bid_price:,} VND on {auction.auction_name}",
        is_read=False,
        is_sent=False,
        created_at=datetime.utcnow()
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def update_notification_status(db: Session, notification_id: int, is_read: bool = True) -> models.Notification | None:
    """Update notification read status"""
    db_notification = get_notification(db, notification_id)
    if not db_notification:
        return None
    
    db_notification.is_read = is_read
    if is_read:
        db_notification.read_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_notification)
    return db_notification


def mark_all_notifications_read(db: Session, user_id: int) -> bool:
    """Mark all user notifications as read"""
    notifications = get_unread_notifications_by_user(db, user_id, skip=0, limit=1000)
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    return True


def delete_notification(db: Session, notification_id: int) -> bool:
    """Delete notification"""
    db_notification = get_notification(db, notification_id)
    if not db_notification:
        return False
    
    db.delete(db_notification)
    db.commit()
    return True


def get_unread_count(db: Session, user_id: int) -> int:
    """Get count of unread notifications for user"""
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()


# ========== WEBSOCKET CONNECTION MANAGEMENT ========== #
import asyncio
from typing import Set, Dict
from fastapi import WebSocket

# Global connection storage
active_connections: Dict[int, Set[WebSocket]] = {}
connection_lock = asyncio.Lock()


async def add_connection(user_id: int, websocket: WebSocket):
    """Add WebSocket connection for user"""
    async with connection_lock:
        if user_id not in active_connections:
            active_connections[user_id] = set()
        active_connections[user_id].add(websocket)


async def remove_connection(user_id: int, websocket: WebSocket):
    """Remove WebSocket connection for user"""
    async with connection_lock:
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]


async def send_to_user(user_id: int, message: dict):
    """Send message to specific user via WebSocket"""
    async with connection_lock:
        connections = active_connections.get(user_id, set())
        disconnected = set()
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.add(websocket)
        
        # Remove disconnected connections
        for websocket in disconnected:
            connections.discard(websocket)


async def broadcast_to_auction_participants(db: Session, auction_id: int, message: dict):
    """Send message to all participants in an auction"""
    # Get all users who have bid on this auction
    bids = get_bids_by_auction(db, auction_id)
    user_ids = set(bid.user_id for bid in bids)
    
    # Send to each participant
    for user_id in user_ids:
        await send_to_user(user_id, message)


# Notification service functions
async def create_and_send_notification(db: Session, notification: schemas.NotificationCreate, websocket_message: dict = None):
    """Create notification and send via WebSocket"""
    db_notification = create_notification(db, notification)
    if not db_notification:
        return None
    
    # Send via WebSocket if message provided
    if websocket_message:
        await send_to_user(notification.user_id, websocket_message)
    
    return db_notification


async def notify_bid_outbid(db: Session, auction_id: int, outbid_user_id: int, new_bidder_id: int, new_bid_price: int):
    """Create and send outbid notification"""
    # Create notification
    notification = create_outbid_notification(db, auction_id, outbid_user_id, new_bidder_id, new_bid_price)
    
    if notification:
        # Get auction and bidder info for WebSocket message
        auction = get_auction(db, auction_id)
        new_bidder = get_account_by_id(db, new_bidder_id)
        
        websocket_message = {
            "type": "bid_outbid",
            "data": {
                "auction_id": auction_id,
                "auction_name": auction.auction_name if auction else "Auction",
                "new_bid_price": new_bid_price,
                "new_bidder_name": f"{new_bidder.first_name} {new_bidder.last_name}".strip() if new_bidder else "Someone",
                "notification_id": notification.notification_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await send_to_user(outbid_user_id, websocket_message)
    
    return notification

