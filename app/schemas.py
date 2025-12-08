from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ========== ENUMS ========== #
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


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
    accountID: int
    username: str
    email: str
    firstName: str
    lastName: str
    phoneNumber: Optional[str] = None
    dateOfBirth: Optional[date] = None
    address: Optional[str] = None
    role: UserRole
    status: AccountStatus
    lastLoginAt: Optional[datetime] = None
    isAuthenticated: bool

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
    firstName: str
    lastName: str
    phoneNumber: Optional[str] = None
    dateOfBirth: Optional[date] = None
    address: Optional[str] = None


class AccountUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[EmailStr] = None
    dateOfBirth: Optional[date] = None
    address: Optional[str] = None


# ========== PRODUCT SCHEMAS ========== #
class ProductBase(BaseModel):
    productName: str
    productDescription: Optional[str] = None
    productType: Optional[str] = None
    
    # Image fields - essential for auction system
    imageUrl: Optional[str] = None  # Main product image URL
    additionalImages: Optional[List[str]] = None  # List of additional image URLs


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    productID: int
    shippingStatus: Optional[str] = None
    approvalStatus: Optional[str] = None
    rejectionReason: Optional[str] = None
    suggestedByUserID: Optional[int] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    productName: Optional[str] = None
    productDescription: Optional[str] = None
    productType: Optional[str] = None
    imageUrl: Optional[str] = None
    additionalImages: Optional[List[str]] = None
    shippingStatus: Optional[str] = None
    approvalStatus: Optional[str] = None
    rejectionReason: Optional[str] = None


class ProductRejectRequest(BaseModel):
    rejectionReason: str


# ========== AUCTION SCHEMAS ========== #
class AuctionBase(BaseModel):
    auctionName: str
    productID: int
    startDate: datetime
    endDate: datetime
    priceStep: int


class AuctionCreate(AuctionBase):
    pass


class Auction(AuctionBase):
    auctionID: int
    auctionStatus: Optional[str] = None
    bidWinnerID: Optional[int] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuctionUpdate(BaseModel):
    auctionName: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    priceStep: Optional[int] = None
    auctionStatus: Optional[str] = None
    bidWinnerID: Optional[int] = None


class AuctionDetail(Auction):
    product: Product = None
    bids: List["Bid"] = []
    currentPrice: Optional[int] = None

    class Config:
        from_attributes = True


class AuctionSearch(BaseModel):
    auctionName: Optional[str] = None
    auctionStatus: Optional[str] = None
    productType: Optional[str] = None
    minPriceStep: Optional[int] = None
    maxPriceStep: Optional[int] = None


# ========== BID SCHEMAS ========== #
class BidBase(BaseModel):
    auctionID: int
    bidPrice: int


class BidCreate(BidBase):
    pass


class Bid(BidBase):
    bidID: int
    userID: int
    bidStatus: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True


# ========== PAYMENT SCHEMAS ========== #
class PaymentBase(BaseModel):
    auctionID: int
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    userAddress: Optional[str] = None
    userReceivingOption: Optional[str] = None
    userPaymentMethod: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    paymentID: int
    userID: int
    paymentStatus: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentStatusUpdate(BaseModel):
    paymentStatus: str


class ProductStatusUpdate(BaseModel):
    shippingStatus: str


class AuctionResultUpdate(BaseModel):
    bidWinnerID: int


# ========== PARTICIPATION SCHEMAS ========== #
class AuctionParticipation(BaseModel):
    auctionID: int
    userID: int
    depositAmount: Optional[int] = None
    participationStatus: Optional[str] = None
    createdAt: datetime

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
    userID: int
    auctionID: int
    notificationType: str
    title: str
    message: str


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase):
    notificationID: int
    isRead: bool
    isSent: bool
    createdAt: datetime
    readAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    isRead: Optional[bool] = None


# ========== WEBSOCKET SCHEMAS ========== #
class WebSocketMessage(BaseModel):
    type: str  # bid_update, notification, auction_status, etc.
    data: dict
    timestamp: datetime = datetime.utcnow()


class BidUpdateMessage(BaseModel):
    auctionID: int
    highestBidID: int
    highestBidPrice: int
    newBidderID: int
    bidderName: str
    bidCount: int


class AuctionStatusMessage(BaseModel):
    auctionID: int
    status: str
    winnerID: Optional[int] = None
    finalPrice: Optional[int] = None


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
    qrUrl: str
    expiresAt: datetime
    expiresInMinutes: int
    amount: int
    paymentType: str  # "deposit" or "final_payment"


class PaymentTokenStatusResponse(BaseModel):
    """Response for token status check"""
    valid: bool
    paymentID: Optional[int] = None
    userID: Optional[int] = None
    amount: Optional[int] = None
    paymentType: Optional[str] = None
    expiresAt: Optional[datetime] = None
    remainingMinutes: Optional[int] = None
    remainingSeconds: Optional[int] = None
    usedAt: Optional[datetime] = None
    expiredAt: Optional[datetime] = None
    error: Optional[str] = None


class QRCallbackResponse(BaseModel):
    """Response after QR code scan callback"""
    success: bool
    message: str
    paymentID: Optional[int] = None
    amount: Optional[int] = None
    paymentStatus: Optional[str] = None


class DepositPaymentResponse(BaseModel):
    """Response when creating deposit payment"""
    success: bool
    message: str
    paymentID: int
    amount: int
    paymentType: str
    paymentStatus: str
    qrToken: PaymentTokenResponse
