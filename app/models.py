from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from .database import Base


# ------------------ ENUMS ------------------ #
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# ------------------ ACCOUNT ------------------ #
class Account(Base):
    __tablename__ = "account"

    accountID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(256), nullable=False)
    firstName: Mapped[str] = mapped_column(String(100), nullable=False)
    lastName: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    dateOfBirth: Mapped[Optional[date]] = mapped_column(DateTime)
    phoneNumber: Mapped[Optional[str]] = mapped_column(String(12))
    address: Mapped[Optional[str]] = mapped_column(String(256))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False, default=UserRole.USER)
    status: Mapped[AccountStatus] = mapped_column(SqlEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    lastLoginAt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    isAuthenticated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    bids: Mapped[List["Bid"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    wonAuctions: Mapped[List["Auction"]] = relationship(
        back_populates="winner", foreign_keys=lambda: [Auction.bidWinnerID]
    )
    submittedProducts: Mapped[List["Product"]] = relationship(
        back_populates="suggestedBy", foreign_keys=lambda: [Product.suggestedByUserID]
    )


# ------------------ PRODUCT ------------------ #
class Product(Base):
    __tablename__ = "product"

    productID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    productName: Mapped[str] = mapped_column(String(256), nullable=False)
    productDescription: Mapped[Optional[str]] = mapped_column(String(1024))
    productType: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Image fields - essential for auction system
    imageUrl: Mapped[Optional[str]] = mapped_column(String(512))  # Main product image
    additionalImages: Mapped[Optional[str]] = mapped_column(String(2048))  # JSON array of additional image URLs
    
    shippingStatus: Mapped[Optional[str]] = mapped_column(String(100))
    approvalStatus: Mapped[Optional[str]] = mapped_column(String(50), default="pending")  # pending, approved, rejected
    rejectionReason: Mapped[Optional[str]] = mapped_column(String(1024))
    suggestedByUserID: Mapped[Optional[int]] = mapped_column(ForeignKey("account.accountID"))
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    auctions: Mapped[List["Auction"]] = relationship(back_populates="product")
    suggestedBy: Mapped[Optional["Account"]] = relationship(
        back_populates="submittedProducts", foreign_keys=[suggestedByUserID]
    )


# ------------------ AUCTION ------------------ #
class Auction(Base):
    __tablename__ = "auction"

    auctionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auctionName: Mapped[str] = mapped_column(String(256), nullable=False)
    productID: Mapped[int] = mapped_column(ForeignKey("product.productID"), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    startDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    endDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    priceStep: Mapped[int] = mapped_column(Integer, nullable=False)
    auctionStatus: Mapped[Optional[str]] = mapped_column(String(100))
    bidWinnerID: Mapped[Optional[int]] = mapped_column(ForeignKey("account.accountID"))

    product: Mapped["Product"] = relationship(back_populates="auctions")
    bids: Mapped[List["Bid"]] = relationship(back_populates="auction", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="auction", cascade="all, delete-orphan")
    winner: Mapped[Optional["Account"]] = relationship(back_populates="wonAuctions")


# ------------------ BID ------------------ #
class Bid(Base):
    __tablename__ = "bid"

    bidID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auctionID: Mapped[int] = mapped_column(ForeignKey("auction.auctionID"), nullable=False, index=True)
    userID: Mapped[int] = mapped_column(ForeignKey("account.accountID"), nullable=False, index=True)
    bidPrice: Mapped[int] = mapped_column(Integer, nullable=False)
    bidStatus: Mapped[Optional[str]] = mapped_column(String(100))
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    auction: Mapped["Auction"] = relationship(back_populates="bids")
    user: Mapped["Account"] = relationship(back_populates="bids")


# ------------------ PAYMENT ------------------ #

class Payment(Base):
    __tablename__ = "payment"

    paymentID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auctionID: Mapped[int] = mapped_column(ForeignKey("auction.auctionID"), nullable=False, index=True)
    userID: Mapped[int] = mapped_column(ForeignKey("account.accountID"), nullable=False, index=True)

    # Replaced user_fullname:
    firstName: Mapped[Optional[str]] = mapped_column(String(100))
    lastName: Mapped[Optional[str]] = mapped_column(String(100))

    userAddress: Mapped[Optional[str]] = mapped_column(String(256))
    userReceivingOption: Mapped[Optional[str]] = mapped_column(String(256))
    userPaymentMethod: Mapped[Optional[str]] = mapped_column(String(100))
    paymentStatus: Mapped[Optional[str]] = mapped_column(String(100))
    
    # NEW FIELDS FOR QR PAYMENT SYSTEM:
    paymentType: Mapped[str] = mapped_column(String(50), nullable=False, default="final_payment")  # "deposit" or "final_payment"
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Payment amount in VND
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    auction: Mapped["Auction"] = relationship(back_populates="payments")
    user: Mapped["Account"] = relationship(back_populates="payments")
    tokens: Mapped[List["PaymentToken"]] = relationship(back_populates="payment", cascade="all, delete-orphan")


# ------------------ PAYMENT TOKEN ------------------ #

class PaymentToken(Base):
    __tablename__ = "payment_token"

    tokenID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    paymentID: Mapped[int] = mapped_column(ForeignKey("payment.paymentID"), nullable=False, index=True)
    userID: Mapped[int] = mapped_column(ForeignKey("account.accountID"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Amount in VND
    expiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    isUsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usedAt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    payment: Mapped["Payment"] = relationship(back_populates="tokens")
    user: Mapped["Account"] = relationship()


# ------------------ NOTIFICATION ------------------ #
class Notification(Base):
    __tablename__ = "notification"

    notificationID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userID: Mapped[int] = mapped_column(ForeignKey("account.accountID"), nullable=False, index=True)
    auctionID: Mapped[int] = mapped_column(ForeignKey("auction.auctionID"), nullable=False, index=True)
    
    notificationType: Mapped[str] = mapped_column(String(50), nullable=False)  # bid_outbid, auction_won, auction_lost, auction_ending, etc.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    isRead: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    isSent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    readAt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    user: Mapped["Account"] = relationship()
    auction: Mapped["Auction"] = relationship()