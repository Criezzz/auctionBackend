from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List

from .database import Base


# ------------------ ACCOUNT ------------------ #
class Account(Base):
    __tablename__ = "account"

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    activated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phone_num: Mapped[Optional[str]] = mapped_column(String(12))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    dob: Mapped[Optional[str]] = mapped_column(String(100))
    is_authenticated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    bids: Mapped[List["Bid"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    won_auctions: Mapped[List["Auction"]] = relationship(
        back_populates="winner", foreign_keys=lambda: [Auction.bid_winner_id]
    )


# ------------------ PRODUCT ------------------ #
class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_description: Mapped[Optional[str]] = mapped_column(String(1024))
    product_type: Mapped[Optional[str]] = mapped_column(String(100))
    shipping_status: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    auctions: Mapped[List["Auction"]] = relationship(back_populates="product")


# ------------------ AUCTION ------------------ #
class Auction(Base):
    __tablename__ = "auction"

    auction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auction_name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    price_step: Mapped[int] = mapped_column(Integer, nullable=False)
    auction_status: Mapped[Optional[str]] = mapped_column(String(100))
    bid_winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))

    product: Mapped["Product"] = relationship(back_populates="auctions")
    bids: Mapped[List["Bid"]] = relationship(back_populates="auction", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="auction", cascade="all, delete-orphan")
    winner: Mapped[Optional["Account"]] = relationship(back_populates="won_auctions")


# ------------------ BID ------------------ #
class Bid(Base):
    __tablename__ = "bid"

    bid_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auction.auction_id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"), nullable=False, index=True)
    bid_price: Mapped[int] = mapped_column(Integer, nullable=False)
    bid_status: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    auction: Mapped["Auction"] = relationship(back_populates="bids")
    user: Mapped["Account"] = relationship(back_populates="bids")


# ------------------ PAYMENT ------------------ #

class Payment(Base):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auction.auction_id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"), nullable=False, index=True)

    # Replaced user_fullname:
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))

    user_address: Mapped[Optional[str]] = mapped_column(String(256))
    user_receiving_option: Mapped[Optional[str]] = mapped_column(String(256))
    user_payment_method: Mapped[Optional[str]] = mapped_column(String(100))
    payment_status: Mapped[Optional[str]] = mapped_column(String(100))

    auction: Mapped["Auction"] = relationship(back_populates="payments")
    user: Mapped["Account"] = relationship(back_populates="payments")