"""
BankPort - Mock bank API interface for handling deposits and payments
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from . import models, schemas
from . import crud


class BankPort:
    """
    Mock bank interface that handles business logic between database and bank
    """
    
    def __init__(self):
        self.bank_name = "MockBank VietNam"
        self.bank_code = "MB"
    
    def generate_qr_code(self, transaction_id: str, amount: int, description: str = None) -> str:
        """
        Generate mock QR code for transaction
        """
        # Mock QR code data - in real implementation, this would be a proper QR code
        qr_data = {
            "bank_code": self.bank_code,
            "bank_name": self.bank_name,
            "transaction_id": transaction_id,
            "amount": amount,
            "description": description or "Auction payment",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Mock QR code string (in real app, this would be actual QR code image data)
        qr_string = f"MB://QR?data={transaction_id}&amount={amount}&desc={description or 'Auction payment'}"
        return qr_string
    
    def create_deposit_transaction(self, db: Session, user_id: int, auction_id: int, amount: int) -> Dict[str, Any]:
        """
        Create deposit transaction (đặt cọc)
        For demo: always returns success immediately
        """
        transaction_id = f"DEP_{uuid.uuid4().hex[:12].upper()}"
        
        # Generate QR code
        qr_code = self.generate_qr_code(
            transaction_id=transaction_id,
            amount=amount,
            description=f"Deposit for auction {auction_id}"
        )
        
        # Mock deposit - immediately successful for demo
        deposit_result = {
            "transaction_id": transaction_id,
            "status": "completed",  # Success immediately for demo
            "amount": amount,
            "bank_response": {
                "code": "00",
                "message": "Deposit successful",
                "timestamp": datetime.utcnow().isoformat()
            },
            "qr_code": qr_code,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return deposit_result
    
    def create_payment_transaction(self, db: Session, user_id: int, auction_id: int, amount: int, payment_id: int) -> Dict[str, Any]:
        """
        Create payment transaction (thanh toán)
        For demo: returns pending status with QR code
        """
        transaction_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        
        # Generate QR code
        qr_code = self.generate_qr_code(
            transaction_id=transaction_id,
            amount=amount,
            description=f"Payment for auction {auction_id}"
        )
        
        # Mock payment - returns pending for demo, but will be successful when confirmed
        payment_result = {
            "transaction_id": transaction_id,
            "status": "pending",  # Pending for demo
            "amount": amount,
            "bank_response": {
                "code": "01",
                "message": "Payment pending - scan QR to confirm",
                "timestamp": datetime.utcnow().isoformat()
            },
            "qr_code": qr_code,
            "payment_id": payment_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return payment_result
    
    def process_payment_confirmation(self, db: Session, transaction_id: str, payment_id: int) -> Dict[str, Any]:
        """
        Process payment confirmation (when user scans QR or clicks payment link)
        For demo: returns success
        """
        # Mock payment processing - always successful for demo
        confirmation_result = {
            "transaction_id": transaction_id,
            "payment_id": payment_id,
            "status": "completed",  # Success for demo
            "bank_response": {
                "code": "00",
                "message": "Payment completed successfully",
                "timestamp": datetime.utcnow().isoformat()
            },
            "confirmed_at": datetime.utcnow().isoformat()
        }
        
        return confirmation_result
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get status of a transaction
        """
        # Mock status check - always returns completed for demo
        status_result = {
            "transaction_id": transaction_id,
            "status": "completed",
            "bank_response": {
                "code": "00",
                "message": "Transaction completed",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return status_result
    
    def calculate_deposit_amount(self, auction: models.Auction) -> int:
        """
        Calculate deposit amount based on auction (typically 10% of starting price)
        """
        # Mock calculation: 10% of price_step as deposit
        deposit_amount = max(10000, int(auction.price_step * 0.1))  # Minimum 10,000 VND
        return deposit_amount
    
    def get_payment_amount(self, db: Session, auction: models.Auction) -> int:
        """
        Get payment amount (winning bid amount)
        """
        # Get highest bid to determine payment amount
        highest_bid = crud.get_current_highest_bid(db=db, auction_id=auction.auction_id)
        if highest_bid:
            return highest_bid.bid_price
        return auction.price_step  # Fallback to price_step