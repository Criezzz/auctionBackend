from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ========== EXISTING ITEM SCHEMAS ========== #
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True


# ========== AUTH SCHEMAS ========== #
class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str  
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_num: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    activated: bool
    is_authenticated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== OTP & PASSWORD RECOVERY SCHEMAS ========== #

class OTPVerificationRequest(BaseModel):
    """Request for OTP verification"""
    otp_code: str
    otp_token: str
    username: str


class OTPVerificationResponse(BaseModel):
    """Response for OTP verification"""
    success: bool
    message: str
    remaining_trials: Optional[int] = None
    updated_token: Optional[str] = None


class OTPRegistrationRequest(BaseModel):
    """Request for OTP resend during registration"""
    username: str


class OTPResendResponse(BaseModel):
    """Response for OTP resend request"""
    success: bool
    message: str
    otp_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds


class PasswordRecoveryRequest(BaseModel):
    """Request for password recovery"""
    username: str


class PasswordRecoveryResponse(BaseModel):
    """Response for password recovery request"""
    success: bool
    message: str
    otp_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds


class OTPVerifyPasswordRecoveryRequest(BaseModel):
    """Request for OTP verification during password recovery"""
    otp_code: str
    otp_token: str
    username: str


class ResetTokenResponse(BaseModel):
    """Response for password recovery verification"""
    success: bool
    message: str
    reset_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds


class PasswordResetRequest(BaseModel):
    """Request for password reset"""
    reset_token: str
    new_password: str


class PasswordResetResponse(BaseModel):
    """Response for password reset"""
    success: bool
    message: str


class RegistrationWithOTPResponse(BaseModel):
    """Response for registration with OTP verification"""
    success: bool
    message: str
    otp_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[UserResponse] = None


class OTPStatusResponse(BaseModel):
    """Response for OTP token status"""
    valid: bool
    expired: bool
    remaining_trials: int
    purpose: Optional[str] = None
    username: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str = ""


class RateLimitResponse(BaseModel):
    """Response for rate limit status"""
    allowed: bool
    remaining: Optional[int] = None
    reset_time: Optional[datetime] = None
    message: str


# ========== ACCOUNT SCHEMAS ========== #
class AccountCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_num: Optional[str] = None
    date_of_birth: Optional[datetime] = None


class AccountUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_num: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[datetime] = None


# ========== PRODUCT SCHEMAS ========== #
class ProductBase(BaseModel):
    product_name: str
    product_description: Optional[str] = None
    product_type: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    product_id: int
    shipping_status: Optional[str] = None
    approval_status: Optional[str] = None
    rejection_reason: Optional[str] = None
    suggested_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_type: Optional[str] = None
    shipping_status: Optional[str] = None
    approval_status: Optional[str] = None
    rejection_reason: Optional[str] = None


class ProductRejectRequest(BaseModel):
    rejection_reason: str


# ========== AUCTION SCHEMAS ========== #
class AuctionBase(BaseModel):
    auction_name: str
    product_id: int
    start_date: datetime
    end_date: datetime
    price_step: int


class AuctionCreate(AuctionBase):
    pass


class Auction(AuctionBase):
    auction_id: int
    auction_status: Optional[str] = None
    bid_winner_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuctionUpdate(BaseModel):
    auction_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    price_step: Optional[int] = None
    auction_status: Optional[str] = None
    bid_winner_id: Optional[int] = None


class AuctionDetail(Auction):
    product: Product = None
    bids: List["Bid"] = []
    current_price: Optional[int] = None

    class Config:
        from_attributes = True


class AuctionSearch(BaseModel):
    auction_name: Optional[str] = None
    auction_status: Optional[str] = None
    product_type: Optional[str] = None
    min_price_step: Optional[int] = None
    max_price_step: Optional[int] = None


# ========== BID SCHEMAS ========== #
class BidBase(BaseModel):
    auction_id: int
    bid_price: int


class BidCreate(BidBase):
    pass


class Bid(BidBase):
    bid_id: int
    user_id: int
    bid_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== PAYMENT SCHEMAS ========== #
class PaymentBase(BaseModel):
    auction_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_address: Optional[str] = None
    user_receiving_option: Optional[str] = None
    user_payment_method: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    payment_id: int
    user_id: int
    payment_status: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentStatusUpdate(BaseModel):
    payment_status: str


class ProductStatusUpdate(BaseModel):
    shipping_status: str


class AuctionResultUpdate(BaseModel):
    bid_winner_id: int


# ========== PARTICIPATION SCHEMAS ========== #
class AuctionParticipation(BaseModel):
    auction_id: int
    user_id: int
    deposit_amount: Optional[int] = None
    participation_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== RESPONSE SCHEMAS ========== #
class RegistrationCancelRequest(BaseModel):
    """Request for cancelling registration and deleting unactivated account"""
    username: str


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    success: bool = False


# ========== NOTIFICATION SCHEMAS ========== #
class NotificationBase(BaseModel):
    user_id: int
    auction_id: int
    notification_type: str
    title: str
    message: str


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase):
    notification_id: int
    is_read: bool
    is_sent: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


# ========== WEBSOCKET SCHEMAS ========== #
class WebSocketMessage(BaseModel):
    type: str  # bid_update, notification, auction_status, etc.
    data: dict
    timestamp: datetime = datetime.utcnow()


class BidUpdateMessage(BaseModel):
    auction_id: int
    highest_bid_id: int
    highest_bid_price: int
    new_bidder_id: int
    bidder_name: str
    bid_count: int


class AuctionStatusMessage(BaseModel):
    auction_id: int
    status: str
    winner_id: Optional[int] = None
    final_price: Optional[int] = None


# ========== SSE SCHEMAS ========== #
class SSEEvent(BaseModel):
    event: str  # bid_update, notification, system_message
    data: dict
    id: Optional[str] = None
    retry: Optional[int] = 3000  # Retry timeout in milliseconds


# ========== QR PAYMENT TOKEN SCHEMAS ========== #
class PaymentTokenResponse(BaseModel):
    """Response when generating payment token"""
    token: str
    qr_url: str
    expires_at: datetime
    expires_in_minutes: int
    amount: int
    payment_type: str  # "deposit" or "final_payment"


class PaymentTokenStatusResponse(BaseModel):
    """Response for token status check"""
    valid: bool
    payment_id: Optional[int] = None
    user_id: Optional[int] = None
    amount: Optional[int] = None
    payment_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    remaining_minutes: Optional[int] = None
    remaining_seconds: Optional[int] = None
    used_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    error: Optional[str] = None


class QRCallbackResponse(BaseModel):
    """Response after QR code scan callback"""
    success: bool
    message: str
    payment_id: Optional[int] = None
    amount: Optional[int] = None
    payment_status: Optional[str] = None


class DepositPaymentResponse(BaseModel):
    """Response when creating deposit payment"""
    success: bool
    message: str
    payment_id: int
    amount: int
    payment_type: str
    payment_status: str
    qr_token: PaymentTokenResponse

