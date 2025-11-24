# Auction Backend API - Frontend Developer Guide

## 🔐 Authentication & Authorization

### Authentication Flow v2.0
**NEW FEATURES**: Email verification with OTP, password recovery, and enhanced security

All protected endpoints require JWT tokens in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Types
1. **Access Token** (JWT): Used for API authentication, expires in 30 minutes
2. **Refresh Token** (JWT): Used to get new access tokens, expires in 7 days
3. **OTP Token** (JWT): Contains OTP code for email verification, expires in 5 minutes
4. **Reset Token** (JWT): Used for password recovery, expires in 5 minutes

### OTP Authentication Flow
**Registration with Email Verification:**
```
1. POST /auth/register → Create account + send OTP email
2. Store otp_token in localStorage
3. POST /auth/register/verify → Verify OTP code
4. Account activated → Return access/refresh tokens for auto-login
```

**Password Recovery:**
```
1. POST /auth/recover → Send OTP for password recovery
2. Store otp_token in localStorage  
3. POST /auth/recover/verify → Verify OTP → get reset_token
4. POST /auth/reset → Use reset_token to set new password
```

### Rate Limiting
- **Registration**: No rate limiting (removed)
- **Login**: 5 attempts/15min per IP
- **OTP Resend**: 3 requests/15min per IP
- **Password Recovery**: 3 requests/15min per IP

## 📡 Complete Endpoint Reference

### 1. Authentication (`/auth`) - Enhanced v2.0

#### NEW: POST /auth/register
```javascript
// Register new account with OTP email verification
// Request
{
  "username": "newuser123",
  "email": "new@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_num": "+1234567890",
  "date_of_birth": "1990-01-01T00:00:00" // optional
}

// Response
{
  "success": true,
  "message": "Tài khoản đã được tạo. Vui lòng kiểm tra email để xác minh OTP.",
  "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "user": {
    "id": 1,
    "username": "newuser123",
    "email": "new@example.com",
    "role": "user",
    "first_name": "John",
    "last_name": "Doe",
    "phone_num": "+1234567890",
    "date_of_birth": "1990-01-01T00:00:00", // optional
    "activated": false,
    "is_authenticated": false,
    "created_at": "2024-01-01T12:00:00"
  }
}
```
**Note**: Account created with `activated=true` (auto-activated for simplicity). OTP sent to email for verification. The system gracefully handles email sending failures and doesn't block registration.

#### NEW: POST /auth/register/verify
```javascript
// Verify OTP code for registration
// Request
{
  "otp_code": "123456",
  "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "newuser123"
}

// Success Response
{
  "success": true,
  "message": "Xác minh email thành công! Tài khoản đã được kích hoạt.",
  "remaining_trials": 5
}

// Failed Response (OTP wrong)
{
  "success": false,
  "message": "Mã OTP không đúng. Bạn còn 4 lần thử.",
  "remaining_trials": 4,
  "updated_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // New token with updated trials
}
```
**Note**: If OTP is wrong, `updated_token` must replace the old token in localStorage.

#### NEW: POST /auth/register/resend
```javascript
// Resend OTP for registration
// Headers: Authorization: Bearer <access_token>
// Request
{
  "username": "newuser123"
}

// Response
{
  "success": true,
  "message": "OTP mới đã được gửi đến email của bạn",
  "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300
}
```
**Rate Limit**: 3 resend requests per 15 minutes per IP

#### NEW: POST /auth/register/cancel
```javascript
// Cancel registration and delete unactivated account
// Request
{
  "username": "newuser123"
}

// Response
{
  "success": true,
  "message": "Tài khoản chưa kích hoạt đã được xóa thành công"
}
```
**Restrictions:**
- Can only delete unactivated accounts (activated=false)
- Account must not have any active bids or participation
- Returns 404 if account doesn't exist
- Returns 400 if account is already activated
- Returns 400 if account has active participation in auctions
- Returns 400 if account has active bids

#### NEW: POST /auth/recover
```javascript
// Request password recovery OTP
// Request
{
  "username": "user123" // Can be username or email
}

// Response
{
  "success": true,
  "message": "OTP khôi phục mật khẩu đã được gửi đến email của bạn",
  "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300
}
```
**Rate Limit**: 3 recovery requests per 15 minutes per IP  
**Security**: Doesn't reveal if user exists or not (security through obscurity)

#### NEW: POST /auth/recover/verify
```javascript
// Verify OTP for password recovery and get reset token
// Request
{
  "otp_code": "123456",
  "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "user123"
}

// Response
{
  "success": true,
  "message": "Xác minh OTP thành công. Bạn có thể đặt lại mật khẩu.",
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300
}
```

#### NEW: POST /auth/reset
```javascript
// Reset password using reset token
// Request
{
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass123!"
}

// Response
{
  "success": true,
  "message": "Mật khẩu đã được đặt lại thành công"
}
```

#### NEW: GET /auth/otp/status
```javascript
// Get OTP token status without verifying OTP code
// Query: ?otp_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

// Response
{
  "valid": true,
  "expired": false,
  "remaining_trials": 5,
  "purpose": "registration",
  "username": "newuser123",
  "expires_at": "2024-01-01T12:05:00",
  "message": "OTP token hợp lệ"
}
```

#### POST /auth/login
```javascript
// Request
{
  "username": "user123",
  "password": "password123"
}

// Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```
**Note**: Store both tokens securely. Use access_token for API calls, refresh_token when access_token expires.

#### POST /auth/refresh
```javascript
// Request
{
  "refresh_token": "eyJ..."
}

// Response
{
  "access_token": "new_eyJ...",
  "refresh_token": "new_eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```
**Note**: Always use the latest refresh_token returned.

#### GET /auth/me
```javascript
// Headers: Authorization: Bearer <access_token>

// Response
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "role": "admin", // or "user"
  "first_name": "John",
  "last_name": "Doe",
  "phone_num": "+1234567890",
  "date_of_birth": "1990-01-01T00:00:00", // optional
  "activated": true,
  "is_authenticated": true,
  "created_at": "2024-01-01T00:00:00"
}
```

#### NEW: POST /auth/logout
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "message": "Đăng xuất thành công", "success": true }
```

### 2. Account Management (`/accounts`)

**IMPORTANT**: Use `/auth/register` for new user registration with OTP verification. The `/accounts/register` endpoint is for legacy compatibility and auto-activates accounts without email verification.

#### POST /accounts/register
```javascript
// Request
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "securepassword",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_num": "+1234567890",
  "date_of_birth": "1992-05-15T00:00:00" // optional
}

// Response: UserResponse object
{
  "id": 1,
  "username": "newuser",
  "email": "new@example.com",
  "role": "user",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_num": "+1234567890",
  "date_of_birth": "1992-05-15T00:00:00", // optional
  "activated": true,
  "is_authenticated": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null // optional
}
```
**Note**: Auto-activates account. In production, email verification would be required.

#### GET /accounts/profile
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Current user's profile (same as /auth/me including date_of_birth and updated_at fields)
```

#### PUT /accounts/profile
```javascript
// Headers: Authorization: Bearer <access_token>

// Request
{
  "first_name": "Updated",
  "last_name": "Name",
  "phone_num": "+0987654321",
  "email": "updated@example.com", // optional
  "date_of_birth": "1991-03-20T00:00:00" // optional
}

// Response: Updated UserResponse
{
  "id": 1,
  "username": "user123",
  "email": "updated@example.com",
  "role": "user",
  "first_name": "Updated",
  "last_name": "Name",
  "phone_num": "+0987654321",
  "date_of_birth": "1991-03-20T00:00:00", // optional
  "activated": true,
  "is_authenticated": true,
  "created_at": "2024-01-01T00:00:00"
}
```
**Note**: Email must be unique if being updated.

### 3. Product Management (`/products`)

#### POST /products/register
```javascript
// Headers: Authorization: Bearer <access_token>

// Request
{
  "product_name": "Premium Figure",
  "product_description": "Limited edition anime figure",
  "product_type": "static" // static, dynamic, remote_control, other
}

// Response
{
  "product_id": 1,
  "product_name": "Premium Figure",
  "product_description": "Limited edition anime figure",
  "product_type": "static",
  "shipping_status": null,
  "approval_status": "pending",
  "rejection_reason": null,
  "suggested_by_user_id": 1,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null
}
```
**Note**: Creates product in pending status for admin approval.

#### GET /products
```javascript
// Query Parameters: ?skip=0&limit=100
// Response: Array of Product objects
```

#### GET /products/{product_id}
```javascript
// Path: product_id (integer)
// Response: Product object
```

#### PUT /products/{product_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "product_name": "Updated Name",
  "shipping_status": "shipped" // pending, approved, rejected, sold, shipped
}

// Response: Updated Product object
```

#### DELETE /products/{product_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: { "message": "Product deleted successfully", "success": true }
```

#### GET /products/pending/approval
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: Array of products pending approval
```

#### POST /products/{product_id}/approve
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: { "message": "Product approved successfully", "success": true }
```

#### NEW: POST /products/{product_id}/reject
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "rejection_reason": "Product does not meet quality standards"
}

// Response: { "message": "Product rejected", "success": true }
```

### 4. Auction Management (`/auctions`)

#### POST /auctions/register
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "auction_name": "Special Figure Auction",
  "product_id": 1,
  "start_date": "2024-01-15T10:00:00", // ISO 8601 format
  "end_date": "2024-01-15T12:00:00",
  "price_step": 10000 // Minimum bid increment in VND
}

// Response: Auction object
```
**Important**: 
- `start_date` and `end_date` must be in ISO 8601 format
- `end_date` must be after `start_date`
- Only admin can create auctions

#### GET /auctions
```javascript
// Query Parameters: ?skip=0&limit=100
// Response: Array of Auction objects
```

#### GET /auctions/{auction_id}
```javascript
// Response: Detailed Auction object with product and bid information
{
  "auction_id": 1,
  "auction_name": "Special Figure Auction",
  "product": { /* Product object */ },
  "bids": [ /* Array of Bid objects */ ],
  "current_price": 50000,
  // ... other auction fields
}
```

#### PUT /auctions/{auction_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "auction_name": "Updated Name",
  "start_date": "2024-01-16T10:00:00",
  "auction_status": "active"
}
```

#### DELETE /auctions/{auction_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: { "message": "Auction deleted successfully", "success": true }
```
**Restrictions**:
- Cannot delete if auction has started
- Cannot delete if there are existing bids
- Cannot delete within 30 minutes of start time

#### NEW: GET /auctions/registered/list
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: Array of auctions with 'registered' or 'pending' status
```

### 5. Bidding (`/bids`)

#### POST /bids/place - UPDATED
```javascript
// Headers: Authorization: Bearer <access_token>

// Request
{
  "auction_id": 1,
  "bid_price": 60000 // Must be higher than current highest + price_step
}

// Response: Bid object
```
**Validation Rules**:
- **NEW**: User must have completed deposit payment (payment_type="deposit", payment_status="completed")
- Bid must be at least `current_highest + price_step`
- Auction must be active (between start_date and end_date)
- Auto-extends auction by 5 minutes if bid placed in last 5 minutes

**Error if no deposit**:
```javascript
{
  "detail": "You must register and pay the deposit before placing bids. Please register for participation first."
}
```

#### POST /bids/cancel/{bid_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "message": "Bid cancelled successfully", "success": true }
```
**Restrictions**:
- Can only cancel your own bids
- Cannot cancel if leading in last 10 minutes
- Cannot cancel after auction ends

#### GET /bids/my-bids
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of user's bid history
```

#### GET /bids/auction/{auction_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of all bids for the auction
```

#### GET /bids/auction/{auction_id}/highest
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Current highest bid object
```

#### NEW: POST /bids/auction/{auction_id}/my-status
```javascript
// Headers: Authorization: Bearer <access_token>

// Response
{
  "has_bids": true,
  "is_leading": false,
  "total_bids": 3,
  "highest_bid": 60000,
  "latest_bid": "2024-01-01T12:30:00",
  "auction_status": "active",
  "time_remaining": 3600
}
```

### 6. Participation (`/participation`)

#### POST /participation/register - UPDATED
```javascript
// Headers: Authorization: Bearer <access_token>

// Request Body: { "auction_id": 1 }

// Response
{
  "message": "Successfully registered for auction. Deposit payment created. Payment ID: 456. Please check your email for payment instructions."
}
```
**NEW BEHAVIOR**: 
- Creates deposit Payment record (payment_type="deposit")
- Deposit amount = `auction.price_step * 10`
- Generates QR payment token (5 min expiry)
- Sends email with QR code for payment
- User must complete deposit payment before placing bids

**Validation**:
- Auction must not have started yet
- User cannot register twice for same auction
- Maximum 50 participants per auction

#### POST /participation/unregister
```javascript
// Headers: Authorization: Bearer <access_token>

// Request Body: { "auction_id": 1 }
// Response: { "message": "Successfully unregistered from auction. Deposit will be refunded.", "success": true }
```
**Restrictions**:
- Cannot unregister after auction starts
- Cannot unregister after placing bids
- Cannot unregister if leading in last 10 minutes

#### GET /participation/my-registrations
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of user's auction registrations with status
```

#### GET /participation/auction/{auction_id}/participants
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: Array of auction participants with statistics
```

#### NEW: GET /participation/auction/{auction_id}/status
```javascript
// Headers: Authorization: Bearer <access_token>

// Response
{
  "is_registered": true,
  "is_leading": false,
  "total_bids": 2,
  "highest_bid": 50000,
  "latest_bid": 45000,
  "registration_date": "2024-01-01T10:00:00",
  "auction_status": "active"
}
```

### 7. Payment Management (`/payments`)

#### POST /payments/create - UPDATED
```javascript
// Headers: Authorization: Bearer <access_token>

// Request
{
  "auction_id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "user_address": "123 Main St, City, Country",
  "user_receiving_option": "shipping", // shipping, pickup
  "user_payment_method": "bank_transfer" // bank_transfer, credit_card, cash
}

// Response: Payment object with QR payment info
{
  "payment_id": 789,
  "auction_id": 1,
  "user_id": 45,
  "first_name": "John",
  "last_name": "Doe",
  "user_address": "123 Main St, City, Country",
  "user_receiving_option": "shipping",
  "user_payment_method": "bank_transfer",
  "payment_status": "pending",
  "payment_type": "final_payment", // NEW
  "amount": 1500000, // NEW - Final winning bid amount
  "created_at": "2024-01-01T12:00:00" // NEW
}
```
**NEW BEHAVIOR**:
- Only auction winner can create payment
- Generates QR payment token (24h expiry)
- Sends email with QR code for final payment
- Sets payment_type="final_payment"
- Amount = Final winning bid amount (not deposit)

**Note**: Payment record is created with status="pending". User must scan QR to complete payment.

#### GET /payments/my-payments
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of user's payments
```

#### GET /payments/auction/{auction_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Payment for specific auction
```

#### GET /payments/{payment_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Payment object
```

#### PUT /payments/{payment_id}/status
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "payment_status": "completed" // pending, processing, completed, failed, cancelled
}

// Response: Updated Payment object
```

#### GET /payments/all/pending
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: Array of pending payments
```

#### POST /payments/{payment_id}/process
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "message": "Payment processed successfully", "success": true }
```
**Note**: Simulates payment processing. Updates status from pending to completed.

#### NEW: GET /payments/status/{status}
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Example: GET /payments/status/completed
// Response: Array of payments with specified status
```

#### NEW: POST /payments/qr-callback/{token}
```javascript
// QR Payment Callback - Simulates payment gateway callback
// No authentication required (public endpoint)

// Example: POST /payments/qr-callback/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

// Success Response
{
  "success": true,
  "message": "Payment completed successfully",
  "payment_id": 123,
  "payment_status": "completed",
  "amount": 500000,
  "auction_name": "Vintage Camera",
  "payment_type": "deposit" // or "final_payment"
}

// Error Response
{
  "success": false,
  "message": "Token has expired",
  "status_code": 400
}
```
**Use Case**: This endpoint is called when user scans QR code or clicks payment link. It validates the token, updates payment status, and sends confirmation email.

**Token Types**:
- **Deposit Token**: Valid for 5 minutes (auction registration)
- **Payment Token**: Valid for 24 hours (final payment after winning)

#### NEW: GET /payments/token/{token}/status
```javascript
// Check payment token status
// No authentication required (public endpoint)

// Example: GET /payments/token/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.../status

// Response
{
  "valid": true,
  "payment_id": 123,
  "user_id": 45,
  "amount": 500000,
  "expires_at": "2024-01-01T13:00:00",
  "remaining_minutes": 3,
  "remaining_seconds": 180,
  "error": null
}

// Invalid Token Response
{
  "valid": false,
  "payment_id": null,
  "user_id": null,
  "amount": 0,
  "expires_at": null,
  "remaining_minutes": 0,
  "remaining_seconds": 0,
  "error": "Token has expired"
}
```
**Use Case**: Frontend polls this endpoint to show countdown timer and token validity on payment page.

### 7.1 QR Payment Flow (NEW)

**Overview**: The system implements time-sensitive QR payment tokens for auction deposits and final payments.

**Payment Types**:
1. **Deposit Payment** (5 min expiry): Required to participate in auction
   - Amount: `auction.price_step * 10`
   - Generated on: POST /participation/register
   - QR sent via email + displayed on web
   
2. **Final Payment** (24h expiry): Required after winning auction
   - Amount: Final winning bid amount
   - Generated on: POST /payments/create
   - QR sent via email + displayed on web

**Complete Flow - Deposit Payment**:
```javascript
// 1. User registers for auction participation
POST /participation/register
Body: { "auction_id": 123 }

// 2. System creates deposit Payment record with payment_type="deposit"
// 3. System generates QR token (5 min expiry)
// 4. System sends email with QR code
// 5. Response includes payment details
Response: {
  "message": "Successfully registered for auction. Deposit payment created. Payment ID: 456. Please check your email for payment instructions."
}

// 6. Frontend displays QR code or redirects to payment page
// 7. User scans QR or clicks link
GET /payments/token/{token}/status // Check token validity

// 8. User confirms payment
POST /payments/qr-callback/{token}

// 9. System marks payment as completed, invalidates token
// 10. User receives confirmation email
// 11. User can now place bids
```

**Complete Flow - Final Payment**:
```javascript
// 1. User wins auction (automatic at auction end)
// 2. User creates final payment
POST /payments/create
Body: {
  "auction_id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "user_address": "123 Main St",
  "user_receiving_option": "shipping",
  "user_payment_method": "bank_transfer"
}

// 3. System creates Payment with payment_type="final_payment"
// 4. System generates QR token (24h expiry)
// 5. System sends email with QR code
// 6. Response includes payment details
Response: Payment object with payment_type="final_payment"

// 7-11. Same as deposit payment flow
```

**Token Validation**:
```javascript
// Token structure (JWT)
{
  "payment_id": 456,
  "user_id": 45,
  "amount": 500000,
  "payment_type": "deposit", // or "final_payment"
  "exp": 1704114600 // Expiration timestamp
}

// Token is validated against database:
// - Must exist in PaymentToken table
// - Must not be used (is_used=false)
// - Must not be expired (expires_at > now)
// - Payment must still be pending
```

**Error Cases**:
- Token expired → Show "QR code expired, please request new one"
- Token already used → Show "Payment already completed"
- Payment already completed → Show success message
- Invalid token → Show "Invalid payment link"

**Frontend Integration**:
See `QR_PAYMENT_FRONTEND_GUIDE.md` for complete React implementation examples.

### 8. Search & Filter (`/search`)

#### POST /search/auctions
```javascript
// Headers: Authorization: Bearer <access_token>

// Request
{
  "auction_name": "figure",
  "auction_status": "active",
  "product_type": "static",
  "min_price_step": 10000,
  "max_price_step": 100000
}

// Response: Array of matching auctions
```

#### GET /search/auctions
```javascript
// Query Parameters:
// ?auction_name=figure&auction_status=active&product_type=static&min_price_step=10000&max_price_step=100000
// Response: Array of matching auctions
```

#### GET /search/auctions/status/{status}
```javascript
// Common statuses: pending, active, completed, cancelled
// Response: Array of auctions with specified status
```

#### GET /search/products/type/{product_type}
```javascript
// Response: Array of products with specified type
```

#### GET /search/auctions/price-range
```javascript
// Query Parameters: ?min_price=10000&max_price=100000
// Response: Array of auctions within price range
```

#### GET /search/auctions/upcoming
```javascript
// Response: Array of upcoming auctions (not started yet)
```

#### GET /search/auctions/active
```javascript
// Response: Array of currently active auctions
```

#### GET /search/auctions/ended
```javascript
// Response: Array of ended auctions
```

### 9. Status Management (`/status`)

#### PUT /status/product/{product_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "shipping_status": "shipped" // pending, approved, rejected, sold, shipped, delivered
}

// Response: Updated Product object
```

#### PUT /status/auction/{auction_id}/result
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only

// Request
{
  "bid_winner_id": 123
}

// Response: Updated Auction object
```
**Note**: Can only update after auction ends.

#### GET /status/product/{product_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Comprehensive product status including auction and payment info
```
**Permissions**: 
- Admin: Full details
- Winner: Detailed status
- Others: Basic status only

#### GET /status/auction/{auction_id}/complete
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Comprehensive auction completion status
```
**Permissions**: Admin and winner only.

#### POST /status/auction/{auction_id}/finalize
```javascript
// Headers: Authorization: Bearer <access_token>
// Note: Admin only
// Response: { "message": "Auction finalized. Winner: User 123, Final price: 50000 VND", "success": true }
```

### 10. Mock Bank API (`/bank`)

Mock bank interface for handling deposits and payments with QR code functionality.

#### GET /bank/health
```javascript
// Health check endpoint
// Response: 
{
  "success": true,
  "message": "Mock Bank API is running",
  "data": {
    "bank_name": "MockBank VietNam",
    "bank_code": "MB",
    "status": "healthy",
    "timestamp": "2025-11-19T09:27:30.000Z"
  }
}
```

#### GET /bank/banks
```javascript
// Get list of supported banks
// Response:
{
  "success": true,
  "data": [
    {
      "bank_code": "MB",
      "bank_name": "MockBank VietNam",
      "status": "active",
      "qr_support": true
    },
    {
      "bank_code": "VCB",
      "bank_name": "Vietcombank", 
      "status": "active",
      "qr_support": true
    }
  ]
}
```

#### GET /bank/terms
```javascript
// Get terms and conditions
// Response:
{
  "success": true,
  "data": {
    "title": "Điều khoản sử dụng",
    "content": "Các điều khoản sử dụng: - Nhóm 7 - Nhóm 7 - Nhóm 7\n...",
    "version": "1.0.0",
    "last_updated": "2025-11-19T09:24:30.000Z"
  }
}
```

#### POST /bank/deposit/create
```javascript
// Create deposit for auction participation (Đặt cọc)
// Headers: Authorization: Bearer <access_token>
// Query Parameters: ?auction_id=1

// Response:
{
  "success": true,
  "message": "Deposit created successfully",
  "data": {
    "transaction_id": "DEP_ABC123DEF456",
    "auction_id": 1,
    "amount": 10000,
    "status": "completed",
    "qr_code": "MB://QR?data=DEP_ABC123DEF456&amount=10000&desc=Deposit for auction 1",
    "bank_info": {
      "bank_name": "MockBank VietNam",
      "bank_code": "MB"
    },
    "created_at": "2025-11-19T09:27:30.000Z"
  }
}
```

#### GET /bank/deposit/status/{transaction_id}
```javascript
// Check deposit transaction status
// Headers: Authorization: Bearer <access_token>

// Response:
{
  "success": true,
  "data": {
    "transaction_id": "DEP_ABC123DEF456",
    "status": "completed",
    "bank_response": {
      "code": "00",
      "message": "Transaction completed",
      "timestamp": "2025-11-19T09:27:30.000Z"
    }
  }
}
```

#### POST /bank/payment/create
```javascript
// Create payment for won auction (Thanh toán)
// Headers: Authorization: Bearer <access_token>

// Request:
{
  "auction_id": 1,
  "payment_id": 123
}

// Response:
{
  "success": true,
  "message": "Payment created - scan QR code to confirm",
  "data": {
    "transaction_id": "PAY_ABC123DEF456",
    "payment_id": 123,
    "auction_id": 1,
    "amount": 60000,
    "status": "pending",
    "qr_code": "MB://QR?data=PAY_ABC123DEF456&amount=60000&desc=Payment for auction 1",
    "bank_info": {
      "bank_name": "MockBank VietNam",
      "bank_code": "MB"
    },
    "payment_instructions": "Scan QR code with banking app or click payment link to complete payment",
    "created_at": "2025-11-19T09:27:30.000Z"
  }
}
```

#### POST /bank/payment/confirm
```javascript
// Confirm payment after QR scan or link click
// Headers: Authorization: Bearer <access_token>

// Request:
{
  "transaction_id": "PAY_ABC123DEF456",
  "payment_id": 123
}

// Response:
{
  "success": true,
  "message": "Payment confirmed successfully",
  "data": {
    "transaction_id": "PAY_ABC123DEF456",
    "payment_id": 123,
    "status": "completed",
    "bank_response": {
      "code": "00",
      "message": "Payment completed successfully",
      "timestamp": "2025-11-19T09:27:30.000Z"
    },
    "confirmed_at": "2025-11-19T09:27:30.000Z"
  }
}
```

#### GET /bank/payment/qr/{transaction_id}
```javascript
// Get QR code for existing payment transaction
// Headers: Authorization: Bearer <access_token>

// Response:
{
  "success": true,
  "data": {
    "transaction_id": "PAY_ABC123DEF456",
    "qr_code": "MB://QR?data=PAY_ABC123DEF456&amount=60000&desc=Auction payment",
    "bank_info": {
      "bank_name": "MockBank VietNam",
      "bank_code": "MB"
    },
    "payment_instructions": "Scan QR code with your banking app to complete payment"
  }
}
```

#### GET /bank/payment/status/{transaction_id}
```javascript
// Check payment transaction status
// Headers: Authorization: Bearer <access_token>

// Response:
{
  "success": true,
  "data": {
    "transaction_id": "PAY_ABC123DEF456",
    "status": "completed",
    "bank_response": {
      "code": "00",
      "message": "Transaction completed",
      "timestamp": "2025-11-19T09:27:30.000Z"
    }
  }
}
```

**Note**: For demo purposes, all deposits are immediately successful, and payments become successful when confirmed.

### 11. Notification Management (`/notifications`)

#### GET /notifications
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of Notification objects
```

#### GET /notifications/unread
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of unread notifications
```

#### GET /notifications/unread/count
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "count": 5 }
```

#### PUT /notifications/{notification_id}/read
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Updated Notification object
```

#### PUT /notifications/mark-all-read
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "message": "All notifications marked as read", "success": true }
```

#### DELETE /notifications/{notification_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "message": "Notification deleted successfully", "success": true }
```

#### GET /notifications/auction/{auction_id}
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: Array of auction-related notifications
```

#### POST /notifications/test
```javascript
// Headers: Authorization: Bearer <access_token>
// Response: { "message": "Test notification created successfully", "success": true }
```

### 12. Server-Sent Events (SSE) (`/sse`)

#### GET /sse/notifications
```javascript
// Connect: EventSource pointing to /sse/notifications
// Requires: Authorization header with Bearer token

// Server events:
event: connected
data: {"timestamp": "2024-01-01T12:00:00"}

event: unread_count
data: {"count": 5}

event: heartbeat
data: {"timestamp": "2024-01-01T12:00:30"}

event: notification
data: {
  "notification_id": 456,
  "type": "bid_outbid",
  "title": "You have been outbid!",
  "message": "John placed a higher bid",
  "auction_id": 789,
  "timestamp": "2024-01-01T12:00:00"
}
```

#### GET /sse/auction/{auction_id}
```javascript
// Connect: EventSource pointing to /sse/auction/{auction_id}
// Requires: Authorization header with Bearer token

event: auction_update
data: {
  "auction_id": 789,
  "auction_name": "Premium Figure Auction",
  "current_price": 50000,
  "bid_count": 10,
  "status": "active",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### GET /sse/test
```javascript
// Test SSE endpoint with sample events
// Response: Stream of test events
```

#### GET /sse/status
```javascript
// Get SSE connection status and available streams
// Response:
{
  "user_id": 123,
  "username": "user123",
  "available_streams": [
    "/sse/notifications",
    "/sse/test"
  ],
  "documentation": "See API documentation for SSE implementation details"
}
```

### 13. WebSocket Connections (`/ws`)

#### General Notifications (`/ws/notifications/{token}`)
```javascript
// Connect: ws://localhost:8000/ws/notifications/{access_token}

// Server messages:
{
  "type": "connection_established",
  "data": {
    "user_id": 123,
    "username": "user123",
    "message": "Connected to notification service"
  },
  "timestamp": "2024-01-01T12:00:00"
}

{
  "type": "unread_count",
  "data": {"count": 5},
  "timestamp": "2024-01-01T12:00:00"
}

{
  "type": "bid_outbid",
  "data": {
    "notification_id": 456,
    "auction_id": 789,
    "auction_name": "Premium Figure Auction",
    "previous_bid": 50000,
    "new_bid": 60000,
    "outbidder_name": "John Doe"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

#### Auction-specific Updates (`/ws/auction/{auction_id}/{token}`)
```javascript
// Connect: ws://localhost:8000/ws/auction/{auction_id}/{access_token}

// Server messages:
{
  "type": "auction_initial_data",
  "data": {
    "auction_id": 789,
    "auction_name": "Premium Figure Auction",
    "current_highest_bid": 50000,
    "highest_bidder_name": "John Doe",
    "bid_count": 10,
    "auction_status": "active",
    "end_time": "2024-01-01T13:00:00"
  },
  "timestamp": "2024-01-01T12:00:00"
}

{
  "type": "bid_update",
  "data": {
    "auction_id": 789,
    "auction_name": "Premium Figure Auction",
    "new_highest_bid": 55000,
    "new_highest_bidder": {
      "user_id": 456,
      "username": "bidder123",
      "name": "Jane Smith"
    },
    "total_bids": 11,
    "extended": false,
    "bid_timestamp": "2024-01-01T12:30:00"
  },
  "timestamp": "2024-01-01T12:30:00"
}
```

#### Client Message Types
```javascript
// Ping to keep connection alive
{"type": "ping"}

// Subscribe to auction updates
{"type": "subscribe_auction", "auction_id": 123}

// Unsubscribe from auction updates
{"type": "unsubscribe_auction", "auction_id": 123}
```

### 14. Real-time Communication Features

#### WebSocket Message Types

##### 1. Connection Events
- `connection_established` - WebSocket connection confirmed
- `unread_count` - Number of unread notifications
- `heartbeat` - Keep-alive ping (every 30 seconds)

##### 2. Bid Events
- `bid_update` - New highest bid placed
- `bid_outbid` - User has been outbid
- `bid_placed` - Confirmation of bid placement
- `auction_extended` - Auction time extended

##### 3. Auction Events
- `auction_ending_soon` - Less than 5 minutes remaining
- `auction_ended` - Auction has ended
- `auction_won` - User won the auction
- `auction_lost` - User lost the auction

##### 4. Payment Events
- `payment_required` - Payment needed for won auction
- `payment_completed` - Payment processed
- `payment_failed` - Payment failed

#### SSE Event Types

##### 1. System Events
- `connected` - SSE stream connected
- `heartbeat` - Keep-alive signal
- `disconnected` - Stream closed
- `error` - Connection or stream error

##### 2. Data Events
- `notification` - New notification available
- `auction_update` - Auction status changed
- `bid_update` - Bid information updated

## 🎯 Frontend Implementation Notes

### 1. Error Handling
Always handle these HTTP status codes:
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (invalid/expired token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

### 2. Authentication Flow
```javascript
// Recommended auth flow
const apiClient = {
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    };

    const response = await fetch(endpoint, { ...options, headers });
    
    if (response.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        const newTokens = await this.refreshToken(refreshToken);
        localStorage.setItem('access_token', newTokens.access_token);
        localStorage.setItem('refresh_token', newTokens.refresh_token);
        
        // Retry original request with new token
        headers['Authorization'] = `Bearer ${newTokens.access_token}`;
        return fetch(endpoint, { ...options, headers });
      }
    }
    
    return response;
  }
};
```

### 3. Real-time Updates
For bidding and auction updates, consider implementing:
- WebSocket connections for real-time bid updates
- Polling for auction status changes
- Server-Sent Events for notifications

### 4. Date/Time Handling
All dates are in ISO 8601 format (UTC). Frontend should:
- Convert to local timezone for display
- Handle timezone differences correctly
- Show countdown timers for active auctions

### 5. Form Validation
Client-side validation should mirror server-side rules:
- Username: 3-32 characters, alphanumeric + underscore
- Email: Valid email format
- Password: Minimum 6 characters
- Dates: Must be in future, end_date > start_date
- Bid amounts: Must be higher than current + price_step

### 6. File Upload
Current implementation doesn't include file upload for product images. When implementing:
- Use multipart/form-data for image uploads
- Support common formats: JPG, PNG, WebP
- Implement image compression/resizing
- Add image validation

### 7. Role-based UI
Different UI elements based on user role:

**Admin Features**:
- Create/manage auctions
- Approve/reject products
- Update payment statuses
- View all payment data
- Delete auctions

**User Features**:
- Register for auctions
- Place/cancel bids
- Make payments
- View own data only

### 8. Performance Considerations
- Implement pagination for large data sets
- Cache auction/product data
- Use query parameters for filtering
- Implement loading states for async operations

### 9. Security Notes
- Never store passwords in frontend
- Use HTTPS in production
- Implement rate limiting on client side
- Validate all inputs on client and server
- Sanitize user-generated content

### 10. Testing
Test these scenarios:
- Login/logout flow
- Token expiration and refresh
- Role-based access control
- Bid validation rules
- Payment workflow
- Error handling for all endpoints

### 11. WebSocket Implementation Example
```javascript
class NotificationService {
  constructor(baseUrl, accessToken) {
    this.baseUrl = baseUrl;
    this.accessToken = accessToken;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const wsUrl = `ws://localhost:8000/ws/notifications/${this.accessToken}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connection_established':
        console.log('Connected:', message.data);
        break;
      
      case 'unread_count':
        this.updateUnreadCount(message.data.count);
        break;
      
      case 'bid_outbid':
        this.showOutbidNotification(message.data);
        break;
      
      case 'bid_update':
        this.updateAuctionBids(message.data);
        break;
      
      case 'heartbeat':
        // Handle keep-alive
        break;
      
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  showOutbidNotification(data) {
    // Show toast notification
    toast.warning(`You have been outbid! New bid: ${data.new_bid_price} VND`);
    
    // Update UI
    this.updateBiddingUI(data.auction_id, data.new_bid_price);
    
    // Play sound
    this.playNotificationSound();
  }

  updateAuctionBids(data) {
    // Update auction page with new bid info
    const auctionElement = document.getElementById(`auction-${data.auction_id}`);
    if (auctionElement) {
      auctionElement.querySelector('.current-bid').textContent = `${data.new_highest_bid} VND`;
      auctionElement.querySelector('.bid-count').textContent = data.total_bids;
    }
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }));
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), 3000);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

## 🚀 Getting Started

1. **Base URL**: `http://localhost:8000` (or your deployed URL)
2. **Documentation**: `http://localhost:8000/docs` (Swagger UI)
3. **Authentication**: Start with login, store tokens securely
4. **User Flow**: Register → Login → Browse auctions → Participate → Bid → Pay

For real-time features like bidding, implement WebSocket connections alongside the REST API.

---

**Last Updated**: 2025-11-21 11:25:59 UTC  
**Version**: 2.2  
**Total Endpoints**: 89+ endpoints across 13 categories  
**New Features**: QR Payment System with time-sensitive tokens for deposits (5min) and final payments (24h)  
**Recent Changes**: Updated registration endpoint documentation, clarified OTP verification process