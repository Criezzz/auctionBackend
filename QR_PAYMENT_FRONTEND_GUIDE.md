# QR Payment System - Frontend Integration Guide

## Overview
Hệ thống thanh toán QR code cho 2 loại payment:
1. **Deposit** (Đặt cọc): 5 phút expiry
2. **Final Payment** (Thanh toán đấu giá): 24 giờ expiry

---

## Implementation Status

### ✅ Completed (Backend Ready)
- PaymentToken model
- Payment model extended with `payment_type`, `amount`, `created_at`
- QR token utility functions (generate, verify, invalidate)
- QR payment schemas
- Configuration settings

### 🚧 Pending Implementation
1. Email templates (send_deposit_email, send_payment_email, send_payment_confirmation_email)
2. Payment QR endpoints (qr-callback, token status)
3. Update participation/register endpoint
4. Update bid placement validation
5. Update payment creation endpoint
6. Full API documentation

---

## Database Schema

### Payment Table (Extended)
```sql
payment_type VARCHAR(50) NOT NULL DEFAULT 'final_payment'  -- 'deposit' or 'final_payment'
amount INT NOT NULL DEFAULT 0                               -- Amount in VND
created_at DATETIME NOT NULL                                -- Payment creation time
```

### PaymentToken Table (New)
```sql
token_id INT PRIMARY KEY AUTO_INCREMENT
token VARCHAR(512) UNIQUE NOT NULL INDEX
payment_id INT NOT NULL (FK to payment.payment_id)
user_id INT NOT NULL (FK to account.account_id)
amount INT NOT NULL
expires_at DATETIME NOT NULL
is_used BOOLEAN NOT NULL DEFAULT FALSE
used_at DATETIME NULL
created_at DATETIME NOT NULL
```

---

## API Endpoints (To Be Implemented)

### 1. Register for Auction (Deposit Payment)
```
POST /participation/register
Body: { "auction_id": 1 }
Headers: Authorization: Bearer <access_token>

Response:
{
  "success": true,
  "message": "Đăng ký thành công. Vui lòng thanh toán đặt cọc trong 5 phút.",
  "payment_id": 123,
  "amount": 100000,
  "payment_type": "deposit",
  "payment_status": "pending",
  "qr_token": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "qr_url": "http://localhost:8000/payments/qr-callback/eyJ...",
    "expires_at": "2025-11-21T10:05:00",
    "expires_in_minutes": 5,
    "amount": 100000,
    "payment_type": "deposit"
  }
}
```

**Frontend Actions:**
- Display QR code using `qr_token.qr_url`
- Show countdown timer (5 minutes)
- Show "Pay Now" button for web payment
- Poll token status every 5 seconds

---

### 2. Create Final Payment (After Winning)
```
POST /payments/create
Body: {
  "auction_id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "user_address": "123 Main St",
  "user_receiving_option": "shipping",
  "user_payment_method": "bank_transfer"
}
Headers: Authorization: Bearer <access_token>

Response:
{
  "success": true,
  "message": "Thanh toán được tạo thành công",
  "payment_id": 456,
  "amount": 500000,
  "payment_type": "final_payment",
  "payment_status": "pending",
  "qr_token": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "qr_url": "http://localhost:8000/payments/qr-callback/eyJ...",
    "expires_at": "2025-11-22T10:00:00",
    "expires_in_minutes": 1440,
    "amount": 500000,
    "payment_type": "final_payment"
  }
}
```

**Frontend Actions:**
- Display QR code
- Show countdown timer (24 hours)
- Show "Pay Now" button
- Email also sent with QR code

---

### 3. Check Token Status
```
GET /payments/token/{token}/status

Response (Valid):
{
  "valid": true,
  "payment_id": 123,
  "user_id": 1,
  "amount": 100000,
  "payment_type": "deposit",
  "expires_at": "2025-11-21T10:05:00",
  "remaining_minutes": 3,
  "remaining_seconds": 180
}

Response (Expired):
{
  "valid": false,
  "error": "Token expired",
  "expired_at": "2025-11-21T10:05:00"
}

Response (Already Used):
{
  "valid": false,
  "error": "Token already used",
  "used_at": "2025-11-21T10:03:00"
}
```

**Frontend Actions:**
- Poll this endpoint every 5 seconds
- Update countdown timer
- Show appropriate message if expired/used
- Stop polling if invalid

---

### 4. QR Code Callback (Mock Payment)
```
POST /payments/qr-callback/{token}

Response (Success):
{
  "success": true,
  "message": "Thanh toán thành công",
  "payment_id": 123,
  "amount": 100000,
  "payment_status": "completed"
}

Response (Error):
{
  "success": false,
  "message": "Token đã được sử dụng hoặc hết hạn"
}
```

**Frontend Actions:**
- Redirect to this URL when "Pay Now" clicked
- Or handle QR scan (in mobile app)
- Show success/error message
- Redirect back to appropriate page

---

### 5. Place Bid (Updated with Deposit Check)
```
POST /bids/place
Body: { "auction_id": 1, "bid_price": 150000 }
Headers: Authorization: Bearer <access_token>

Response (No Deposit):
{
  "detail": "Bạn cần đăng ký và thanh toán đặt cọc trước khi đặt giá"
}

Response (Deposit Pending):
{
  "detail": "Vui lòng hoàn tất thanh toán đặt cọc trước khi đặt giá"
}

Response (Success):
{
  "bid_id": 789,
  "auction_id": 1,
  "user_id": 1,
  "bid_price": 150000,
  "bid_status": "active",
  "created_at": "2025-11-21T10:10:00"
}
```

---

## Frontend Implementation Checklist

### Registration & Deposit Flow
- [ ] Call `/participation/register` to register
- [ ] Display QR code from `qr_token.qr_url`
- [ ] Implement 5-minute countdown timer
- [ ] Poll `/payments/token/{token}/status` every 5 seconds
- [ ] Show "Pay Now" button → redirects to `/payments/qr-callback/{token}`
- [ ] Handle payment completion (refresh status, enable bidding)
- [ ] Show appropriate errors (expired, already used)

### Final Payment Flow
- [ ] Call `/payments/create` after winning auction
- [ ] Display QR code from response
- [ ] Implement 24-hour countdown timer
- [ ] Poll token status every 10-30 seconds
- [ ] Show "Pay Now" button
- [ ] Handle payment completion
- [ ] Show confirmation message

### Bid Placement
- [ ] Check deposit status before showing bid form
- [ ] Show deposit requirement message if not paid
- [ ] Enable bid button only after deposit completed
- [ ] Handle deposit validation errors

### UI Components Needed
- [ ] QR Code Display Component (can use qrcode.react library)
- [ ] Countdown Timer Component (with auto-refresh)
- [ ] Payment Status Poller Hook
- [ ] Payment Modal/Page
- [ ] Success/Error Toast Notifications

---

## Example React Hooks

### usePaymentToken Hook
```javascript
import { useState, useEffect } from 'react';
import { api } from './api';

export function usePaymentToken(token) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const checkStatus = async () => {
      try {
        const response = await api.get(`/payments/token/${token}/status`);
        setStatus(response.data);
        setLoading(false);

        // Stop polling if invalid
        if (!response.data.valid) {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Token status check failed:', error);
        setLoading(false);
      }
    };

    // Initial check
    checkStatus();

    // Poll every 5 seconds
    const interval = setInterval(checkStatus, 5000);

    return () => clearInterval(interval);
  }, [token]);

  return { status, loading };
}
```

### Countdown Timer Component
```javascript
import { useState, useEffect } from 'react';

export function CountdownTimer({ expiresAt }) {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    const updateRemaining = () => {
      const now = new Date().getTime();
      const expiry = new Date(expiresAt).getTime();
      const diff = Math.max(0, expiry - now);
      setRemaining(diff);
    };

    updateRemaining();
    const interval = setInterval(updateRemaining, 1000);

    return () => clearInterval(interval);
  }, [expiresAt]);

  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);

  return (
    <div className={`countdown ${remaining < 60000 ? 'warning' : ''}`}>
      {minutes}:{seconds.toString().padStart(2, '0')}
    </div>
  );
}
```

---

## Payment Types & Amounts

### Deposit Amount
- Calculated as: `auction.price_step * 10`
- Example: If price_step = 10,000 VND → deposit = 100,000 VND
- Refunded if user unregisters before auction starts
- Refunded if user doesn't win

### Final Payment Amount
- Equal to winning bid price
- Must be paid within 24 hours
- Non-refundable once paid

---

## Error Handling

### Common Errors
1. **Token Expired**: Show message + option to regenerate
2. **Token Already Used**: Show success message or redirect
3. **Invalid Token**: Show error + contact support
4. **Payment Failed**: Retry option + support contact
5. **Network Error**: Retry mechanism

### User Messages (Vietnamese)
- Deposit: "Vui lòng thanh toán đặt cọc trong 5 phút"
- Expired: "Mã thanh toán đã hết hạn. Vui lòng đăng ký lại"
- Used: "Thanh toán đã được hoàn tất"
- Success: "Thanh toán thành công!"

---

## Security Notes

1. **Never store payment tokens in localStorage** - use sessionStorage or memory
2. **Always validate token on backend** before processing payment
3. **Check payment status** before allowing critical actions (bidding)
4. **Use HTTPS** in production for QR URLs
5. **Implement CORS properly** for API calls

---

## Testing Scenarios

1. **Happy Path**: Register → See QR → Pay → Bid successfully
2. **Timeout**: Register → Wait 6 minutes → Token expires
3. **Double Payment**: Pay on web → Scan QR → Second attempt fails
4. **Concurrent Payment**: Multiple tabs → Only one succeeds
5. **Expired Token**: Try to use old QR code → Error message

---

## Next Steps for Backend

1. Implement email templates in `mailer.py`
2. Add QR callback endpoint in `payments.py` router
3. Update participation registration logic
4. Update bid placement validation
5. Add comprehensive error handling
6. Write unit tests for token generation/validation
7. Update API_ENDPOINTS_GUIDE.md with full documentation
