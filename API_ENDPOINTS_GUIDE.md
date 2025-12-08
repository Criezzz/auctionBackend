# API Endpoints Guide - Auction System

## Tổng quan
Đây là hướng dẫn đầy đủ về các API endpoints và Gateway classes trong Auction System.

**🏷️ QUAN TRỌNG**: Database model attributes đã được refactor theo camelCase convention. Tất cả ID fields đều viết hoa cả 2 chữ (ID thay vì Id).

## Database Model Changes - CamelCase Convention
Các thuộc tính database model đã được refactor:

### Account Model (NEW STRUCTURE)
The Account model has been completely refactored with the following exact structure:

```typescript
interface Account {
    accountID: number;           // Primary key
    username: string;            // Unique username (32 chars)
    password: string;            // Hashed password (256 chars)
    firstName: string;           // First name (100 chars, required)
    lastName: string;            // Last name (100 chars, required)
    email: string;               // Unique email (256 chars)
    dateOfBirth?: date;          // Optional date of birth
    phoneNumber?: string;        // Optional phone number (12 chars)
    address?: string;            // Optional address (256 chars)
    role: UserRole;              // Enum: "user" | "admin"
    status: AccountStatus;       // Enum: "active" | "inactive" | "suspended"
    lastLoginAt?: datetime;      // Optional last login time
    isAuthenticated: boolean;    // Authentication status (OTP verified)
    createdAt: datetime;         // Account creation timestamp (used for wipe-on-demand)
}
```

#### Enums:
- **UserRole**: `USER` (default), `ADMIN`
- **AccountStatus**: `ACTIVE` (default), `INACTIVE`, `SUSPENDED`

**Note**: `createdAt` field is used for wipe-on-demand mechanism (see Registration section)

### Product Model
- `product_id` → `productID`
- `product_name` → `productName`
- `product_description` → `productDescription`
- `product_type` → `productType`
- `image_url` → `imageUrl`
- `additional_images` → `additionalImages`
- `shipping_status` → `shippingStatus`
- `approval_status` → `approvalStatus`
- `rejection_reason` → `rejectionReason`
- `suggested_by_user_id` → `suggestedByUserID`

### Auction Model
- `auction_id` → `auctionID`
- `auction_name` → `auctionName`
- `product_id` → `productID`
- `created_at` → `createdAt`
- `updated_at` → `updatedAt`
- `start_date` → `startDate`
- `end_date` → `endDate`
- `price_step` → `priceStep`
- `auction_status` → `auctionStatus`
- `bid_winner_id` → `bidWinnerID`

### Bid Model
- `bid_id` → `bidID`
- `auction_id` → `auctionID`
- `user_id` → `userID`
- `bid_price` → `bidPrice`
- `bid_status` → `bidStatus`
- `created_at` → `createdAt`

### Payment Model
- `payment_id` → `paymentID`
- `auction_id` → `auctionID`
- `user_id` → `userID`
- `first_name` → `firstName`
- `last_name` → `lastName`
- `user_address` → `userAddress`
- `user_receiving_option` → `userReceivingOption`
- `user_payment_method` → `userPaymentMethod`
- `payment_status` → `paymentStatus`
- `payment_type` → `paymentType`
- `created_at` → `createdAt`

### PaymentToken Model
- `token_id` → `tokenID`
- `payment_id` → `paymentID`
- `user_id` → `userID`
- `expires_at` → `expiresAt`
- `is_used` → `isUsed`
- `used_at` → `usedAt`
- `created_at` → `createdAt`

### Notification Model
- `notification_id` → `notificationID`
- `user_id` → `userID`
- `auction_id` → `auctionID`
- `notification_type` → `notificationType`
- `is_read` → `isRead`
- `is_sent` → `isSent`
- `created_at` → `createdAt`
- `read_at` → `readAt`

## Gateway Classes Overview

### 1. BankPort - Bank API Gateway
**File**: `app/bank_port.py`
**Mô tả**: Class gateway để giao tiếp với dịch vụ ngân hàng bên ngoài (Mock mode)

#### Methods:

**1.1 get_service_status()**
- **Mô tả**: Kiểm tra trạng thái dịch vụ ngân hàng
- **Returns**: 
```json
{
  "service_status": "active",
  "service_name": "Auction System Bank Service",
  "mock_mode": true,
  "supported_banks": ["VCB", "BIDV", "TCB", "CTG"],
  "last_check": "2024-11-30T13:00:00.000Z"
}
```

**1.2 validate_account(account_number, bank_code)**
- **Mô tả**: Xác thực tài khoản ngân hàng
- **Parameters**:
  - `account_number` (str): Số tài khoản
  - `bank_code` (str): Mã ngân hàng (optional)
- **Returns**:
```json
{
  "success": true,
  "message": "Account validated successfully",
  "account_info": {
    "account_number": "123456789",
    "bank_code": "VCB",
    "account_name": "John Doe",
    "account_status": "active"
  },
  "service": "Auction System Bank Service"
}
```

**1.3 get_account_balance(account_number, bank_code)**
- **Mô tả**: Lấy số dư tài khoản
- **Parameters**:
  - `account_number` (str): Số tài khoản
  - `bank_code` (str): Mã ngân hàng (optional)
- **Returns**:
```json
{
  "success": true,
  "message": "Balance retrieved successfully",
  "balance": {
    "account_number": "123456789",
    "bank_code": "VCB",
    "available_balance": 50000000,
    "currency": "VND",
    "last_updated": "2024-11-30T13:00:00.000Z"
  },
  "service": "Auction System Bank Service"
}
```

**1.4 transfer_money(from_account, to_account, amount, description)**
- **Mô tả**: Chuyển tiền giữa các tài khoản
- **Parameters**:
  - `from_account` (str): Tài khoản nguồn
  - `to_account` (str): Tài khoản đích
  - `amount` (int): Số tiền
  - `description` (str): Mô tả giao dịch
- **Returns**:
```json
{
  "success": true,
  "message": "Transfer completed successfully",
  "transaction": {
    "transaction_id": "TXN123456789",
    "from_account": "123456789",
    "to_account": "987654321",
    "amount": 1000000,
    "currency": "VND",
    "description": "Auction deposit payment",
    "status": "completed",
    "timestamp": "2024-11-30T13:00:00.000Z"
  },
  "service": "Auction System Bank Service"
}
```

**1.5 get_transaction_history(account_number, start_date, end_date)**
- **Mô tả**: Lấy lịch sử giao dịch
- **Parameters**:
  - `account_number` (str): Số tài khoản
  - `start_date` (str): Ngày bắt đầu (ISO format)
  - `end_date` (str): Ngày kết thúc (ISO format)
- **Returns**:
```json
{
  "success": true,
  "message": "Transaction history retrieved successfully",
  "transactions": [
    {
      "transaction_id": "TXN123456789",
      "amount": 1000000,
      "type": "credit",
      "description": "Auction deposit payment",
      "timestamp": "2024-11-30T13:00:00.000Z"
    }
  ],
  "total_count": 1,
  "service": "Auction System Bank Service"
}
```

**1.6 check_service_health()**
- **Mô tả**: Kiểm tra sức khỏe dịch vụ
- **Returns**:
```json
{
  "status": "healthy",
  "response_time": 150,
  "uptime": "99.9%",
  "last_check": "2024-11-30T13:00:00.000Z"
}
```

---

### 2. EmailPort - Email Service Gateway
**File**: `app/email_port.py`
**Mô tả**: Class gateway để giao tiếp với dịch vụ email SMTP

#### Methods:

**2.1 get_service_status()**
- **Mô tả**: Kiểm tra trạng thái dịch vụ email
- **Returns**:
```json
{
  "service_status": "active",
  "service_name": "Auction System Email Service",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "tls_enabled": true,
  "last_check": "2024-11-30T13:00:00.000Z"
}
```

**2.2 send_raw_email(subject, content, target_address, is_html, from_name, from_address)**
- **Mô tả**: Gửi email thô qua SMTP
- **Parameters**:
  - `subject` (str): Tiêu đề email
  - `content` (str): Nội dung email
  - `target_address` (str): Địa chỉ người nhận
  - `is_html` (bool): Định dạng HTML hay text (default: True)
  - `from_name` (str): Tên người gửi (optional)
  - `from_address` (str): Địa chỉ người gửi (optional)
- **Returns**:
```json
{
  "success": true,
  "message": "Email sent successfully to user@example.com",
  "recipient": "user@example.com",
  "sent_at": "2024-11-30T13:00:00.000Z",
  "service": "Auction System Email Service"
}
```

**2.3 send_otp_email(otp, username, target_address, request_type)**
- **Mô tả**: Gửi email OTP xác minh
- **Parameters**:
  - `otp` (str): Mã OTP 6 chữ số
  - `username` (str): Tên người dùng
  - `target_address` (str): Địa chỉ email
  - `request_type` (str): Loại yêu cầu ("registration", "password_reset", "email_change")
- **Returns**:
```json
{
  "success": true,
  "message": "OTP email sent successfully to user@example.com",
  "recipient": "user@example.com",
  "sent_at": "2024-11-30T13:00:00.000Z",
  "service": "Auction System Email Service"
}
```

**2.4 send_welcome_email(username, email)**
- **Mô tả**: Gửi email chào mừng sau khi đăng ký thành công
- **Parameters**:
  - `username` (str): Tên người dùng
  - `email` (str): Địa chỉ email
- **Returns**:
```json
{
  "success": true,
  "message": "Welcome email sent successfully to user@example.com",
  "recipient": "user@example.com",
  "sent_at": "2024-11-30T13:00:00.000Z",
  "service": "Auction System Email Service"
}
```

**2.5 send_payment_email(username, email, auction_name, amount, qr_url, expires_at, email_type)**
- **Mô tả**: Gửi email thanh toán (đặt cọc hoặc thanh toán cuối)
- **Parameters**:
  - `username` (str): Tên người dùng
  - `email` (str): Địa chỉ email
  - `auction_name` (str): Tên phiên đấu giá
  - `amount` (int): Số tiền
  - `qr_url` (str): URL QR code
  - `expires_at` (datetime): Thời gian hết hạn
  - `email_type` (str): Loại email ("deposit" hoặc "final_payment")
- **Returns**:
```json
{
  "success": true,
  "message": "Payment email sent successfully to user@example.com",
  "recipient": "user@example.com",
  "sent_at": "2024-11-30T13:00:00.000Z",
  "service": "Auction System Email Service"
}
```

**2.6 send_payment_confirmation_email(username, email, auction_name, payment_amount, payment_type, payment_method)**
- **Mô tả**: Gửi email xác nhận thanh toán thành công
- **Parameters**:
  - `username` (str): Tên người dùng
  - `email` (str): Địa chỉ email
  - `auction_name` (str): Tên phiên đấu giá
  - `payment_amount` (int): Số tiền đã thanh toán
  - `payment_type` (str): Loại thanh toán ("deposit" hoặc "final_payment")
  - `payment_method` (str): Phương thức thanh toán (default: "bank_transfer")
- **Returns**:
```json
{
  "success": true,
  "message": "Payment confirmation email sent successfully to user@example.com",
  "recipient": "user@example.com",
  "sent_at": "2024-11-30T13:00:00.000Z",
  "service": "Auction System Email Service"
}
```

---

## Sử dụng trong ứng dụng

### Import Gateway Classes:
```python
from app.bank_port import bank_port
from app.email_port import email_port
```

### Ví dụ sử dụng BankPort:
```python
# Kiểm tra trạng thái dịch vụ
status = bank_port.get_service_status()
print(f"Service Status: {status['service_status']}")

# Xác thực tài khoản
result = bank_port.validate_account('123456789', 'VCB')
if result['success']:
    print(f"Account validated: {result['account_info']['account_name']}")

# Chuyển tiền
transfer_result = bank_port.transfer_money(
    from_account='123456789',
    to_account='987654321', 
    amount=1000000,
    description='Auction deposit payment'
)
```

### Ví dụ sử dụng EmailPort:
```python
import asyncio
from datetime import datetime, timedelta

async def send_welcome():
    # Gửi email chào mừng
    result = await email_port.send_welcome_email('john_doe', 'john@example.com')
    print(f"Email sent: {result['success']}")

async def send_otp():
    # Gửi OTP
    result = await email_port.send_otp_email(
        otp='123456',
        username='john_doe',
        target_address='john@example.com',
        request_type='registration'
    )
    print(f"OTP sent: {result['success']}")

async def send_payment():
    # Gửi email thanh toán đặt cọc
    result = await email_port.send_payment_email(
        username='john_doe',
        email='john@example.com',
        auction_name='iPhone 15 Pro Max',
        amount=5000000,
        qr_url='https://payment.example.com/qr/123',
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        email_type='deposit'
    )
    print(f"Payment email sent: {result['success']}")

# Chạy các async functions
asyncio.run(send_welcome())
asyncio.run(send_otp())
asyncio.run(send_payment())
```

---

## Cấu hình SMTP cho EmailPort

EmailPort sử dụng cấu hình từ `configs/config_mail.py`. Đảm bảo file này có:

```python
class MailSettings:
    MAIL_HOST = "smtp.gmail.com"          # SMTP server
    MAIL_PORT = 587                        # SMTP port
    MAIL_USE_TLS = True                    # Use TLS
    MAIL_USERNAME = "your-email@gmail.com" # Your email
    MAIL_PASSWORD = "your-app-password"    # App password
    MAIL_FROM_NAME = "Auction System"      # Sender name
    MAIL_FROM_ADDRESS = "noreply@auction.com" # Sender email
    SUPPORT_EMAIL = "support@auction.com"  # Support contact
    MAIL_TIMEOUT = 30                      # Timeout in seconds
```

---

## Lưu ý quan trọng

### 1. BankPort Mock Mode
- Tất cả các endpoint của BankPort đều trả về kết quả thành công mặc định
- Sử dụng cho mục đích demo và testing
- Khi cần tích hợp với ngân hàng thật, cần thay đổi implementation

### 2. EmailPort SMTP
- Sử dụng SMTP thật để gửi email
- Cần cấu hình app password cho Gmail
- Các email templates đều là HTML đẹp với responsive design

### 3. Async/Await
- EmailPort methods đều là async
- Cần sử dụng `await` khi gọi các methods
- Có thể gọi từ async functions hoặc sử dụng `asyncio.run()`

### 4. Error Handling
- Tất cả methods đều trả về dict với `success` field
- Khi có lỗi, `success` = False và có `message` mô tả lỗi
- Log errors được in ra console để debugging

### 5. Security
- OTP emails có thời hạn 5 phút
- Email templates không chứa thông tin nhạy cảm
- SMTP credentials được cấu hình qua environment variables

---

---

## Database Subsystem Implementation

### Tổng quan Database Interfaces
Hệ thống sử dụng **15 Database Interfaces** theo Interface-based Architecture pattern, mapping với 89+ API endpoints và 40+ CRUD operations.

### 1. IAuthDatabase - Authentication Interface
**File**: `app/routers/auth.py`
**CRUD Functions**: `app/crud.py` (4 functions)

#### API Endpoints:
```
POST   /auth/register              - Register with OTP email verification
POST   /auth/register/verify       - Verify OTP for registration  
POST   /auth/register/resend       - Resend OTP for registration
POST   /auth/register/cancel       - Cancel registration (delete unverified account)
POST   /auth/login                 - User login
POST   /auth/refresh               - Refresh access token
POST   /auth/recover               - Request password recovery OTP
POST   /auth/recover/verify        - Verify recovery OTP
POST   /auth/reset                 - Reset password with reset token
POST   /auth/logout                - User logout
GET    /auth/me                    - Get current user info
GET    /auth/otp/status            - Get OTP token status
```

#### Wipe-on-Demand Mechanism (Registration):
The registration endpoint implements a **wipe-on-demand** mechanism to handle cases where:
1. User registers but doesn't verify OTP
2. User exits and tries to register again with the same username/email

**Logic**:
- Uses "INSERT first, catch error later" approach (not "check then insert")
- If IntegrityError occurs (duplicate username/email):
  - Check if existing account is unverified (`isAuthenticated=False`)
  - Check if account is older than **15 minutes** (using `createdAt`)
  - If both conditions met: delete old account and retry registration
  - Otherwise: return appropriate error message

**Configuration**:
- `UNVERIFIED_ACCOUNT_EXPIRY_MINUTES = 15`

**Benefits**:
- Race-condition safe (INSERT first approach)
- Allows users to re-register if they abandoned verification
- Protects verified accounts from being overwritten

#### CRUD Functions:
```python
authenticate_account(db: Session, username: str, password: str) -> models.Account | None
create_account(db: Session, account: schemas.AccountCreate) -> models.Account
get_account_by_username(db: Session, username: str) -> models.Account | None
get_account_by_id(db: Session, account_id: int) -> models.Account | None
update_account(db: Session, account_id: int, account_update: schemas.AccountUpdate) -> models.Account | None
```

---

### 2. IAccountDatabase - User Account Management
**File**: `app/routers/accounts.py`

#### API Endpoints:
```
GET    /accounts/profile           - Get user profile
PUT    /accounts/profile           - Update user profile
```

---

### 3. IProductDatabase - Product Management
**File**: `app/routers/products.py`
**CRUD Functions**: `app/crud.py` (5 functions)

#### API Endpoints:
```
POST   /products/register          - Create new product
GET    /products                   - Get all products with pagination
GET    /products/{product_id}      - Get product by ID
PUT    /products/{product_id}      - Update product
DELETE /products/{product_id}      - Delete product
```

#### CRUD Functions:
```python
get_product(db: Session, product_id: int) -> models.Product | None
get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]
create_product(db: Session, product: schemas.ProductCreate, user_id: int = None) -> models.Product
update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> models.Product | None
delete_product(db: Session, product_id: int) -> bool
```

---

### 4. IImageDatabase - Image Management
**File**: `app/routers/images.py`

#### API Endpoints:
```
POST   /images/upload              - Upload image
GET    /images/{filename}          - Get image
DELETE /images/{filename}          - Delete image
```

---

### 5. IAuctionDatabase - Auction Management
**File**: `app/routers/auctions.py`
**CRUD Functions**: `app/crud.py` (6 functions)

#### API Endpoints:
```
POST   /auctions/register          - Create new auction
GET    /auctions                   - Get all auctions
GET    /auctions/{auction_id}      - Get auction details
PUT    /auctions/{auction_id}      - Update auction
DELETE /auctions/{auction_id}      - Delete auction
```

#### CRUD Functions:
```python
get_auction(db: Session, auction_id: int) -> models.Auction | None
get_auctions(db: Session, skip: int = 0, limit: int = 100) -> List[models.Auction]
create_auction(db: Session, auction: schemas.AuctionCreate) -> models.Auction
update_auction(db: Session, auction_id: int, auction_update: schemas.AuctionUpdate) -> models.Auction | None
delete_auction(db: Session, auction_id: int) -> bool
search_auctions(db: Session, search_params: schemas.AuctionSearch, skip: int = 0, limit: int = 100) -> List[models.Auction]
```

---

### 6. IBidDatabase - Bidding System
**File**: `app/routers/bids.py`
**CRUD Functions**: `app/crud.py` (6 functions)

#### API Endpoints:
```
POST   /bids/place                 - Place new bid
DELETE /bids/{bid_id}/cancel       - Cancel bid
GET    /bids/my-bids               - Get user's bids
GET    /bids/auction/{auction_id}  - Get bids for auction
GET    /bids/highest/{auction_id}  - Get highest bid for auction
```

#### CRUD Functions:
```python
get_bid(db: Session, bid_id: int) -> models.Bid | None
get_bids_by_auction(db: Session, auction_id: int, skip: int = 0, limit: int = 100) -> List[models.Bid]
get_bids_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Bid]
create_bid(db: Session, bid: schemas.BidCreate, user_id: int) -> models.Bid
cancel_bid(db: Session, bid_id: int, user_id: int) -> bool
get_current_highest_bid(db: Session, auction_id: int) -> models.Bid | None
```

---

### 7. IParticipationDatabase - Auction Registration
**File**: `app/routers/participation.py`

#### API Endpoints:
```
POST   /participation/register     - Register for auction
GET    /participation/my-participations - Get user's participations
GET    /participation/auction/{auction_id}/participants - Get auction participants
```

---

### 8. IPaymentDatabase - Payment Management
**File**: `app/routers/payments.py`
**CRUD Functions**: `app/crud.py` (5 functions)

#### API Endpoints:
```
POST   /payments/create            - Create payment
GET    /payments                   - Get user's payments
GET    /payments/{payment_id}      - Get payment details
PUT    /payments/{payment_id}/status - Update payment status
GET    /payments/token/{token}/status - Get QR token status
```

#### CRUD Functions:
```python
get_payment(db: Session, payment_id: int) -> models.Payment | None
get_payments_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Payment]
get_payments_by_auction(db: Session, auction_id: int) -> List[models.Payment]
create_payment(db: Session, payment: schemas.PaymentCreate, user_id: int) -> models.Payment
update_payment_status(db: Session, payment_id: int, status: str) -> models.Payment | None
```

---

### 9. IBankDatabase - Banking Integration ⭐
**File**: `app/routers/bank.py`
**Gateway**: `app/bank_port.py`

#### API Endpoints:
```
GET    /bank/banks                 - Get supported banks
GET    /bank/account/validate      - Validate bank account
GET    /bank/deposit/create        - Create deposit
GET    /bank/deposit/status/{transaction_id} - Check deposit status
POST   /bank/payment/create        - Create payment
GET    /bank/payment/status/{transaction_id} - Check payment status
POST   /bank/payment/confirm       - Confirm payment
GET    /bank/health                - Bank service health check
```

---

### 10. ISearchDatabase - Search & Filtering
**File**: `app/routers/search.py`

#### API Endpoints:
```
POST   /search/auctions            - Search auctions with criteria
GET    /search/auctions/status/{status} - Get auctions by status
GET    /search/products/type/{product_type} - Get products by type
```

---

### 11. INotificationDatabase - Notification System ⭐
**File**: `app/routers/notifications.py`
**CRUD Functions**: `app/crud.py` (9 functions)
**WebSocket Functions**: `app/crud.py` (2 functions)

#### API Endpoints:
```
GET    /notifications              - Get user notifications
GET    /notifications/unread       - Get unread notifications
GET    /notifications/unread/count - Get unread count
PUT    /notifications/{notification_id}/read - Mark notification as read
PUT    /notifications/mark-all-read - Mark all as read
DELETE /notifications/{notification_id} - Delete notification
GET    /notifications/auction/{auction_id} - Get auction-specific notifications
POST   /notifications/test         - Create test notification
```

#### CRUD Functions:
```python
get_notification(db: Session, notification_id: int) -> models.Notification | None
get_notifications_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Notification]
get_unread_notifications_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Notification]
create_notification(db: Session, notification: schemas.NotificationCreate) -> models.Notification
create_outbid_notification(db: Session, auction_id: int, outbid_user_id: int, new_bidder_id: int, new_bid_price: int) -> models.Notification
update_notification_status(db: Session, notification_id: int, is_read: bool = True) -> models.Notification | None
mark_all_notifications_read(db: Session, user_id: int) -> bool
delete_notification(db: Session, notification_id: int) -> bool
get_unread_count(db: Session, user_id: int) -> int
```

#### WebSocket Functions:
```python
create_and_send_notification(db: Session, notification: schemas.NotificationCreate, websocket_message: dict = None)
notify_bid_outbid(db: Session, auction_id: int, outbid_user_id: int, new_bidder_id: int, new_bid_price: int)
```

---

### 12. IStatusDatabase - Status Management
**File**: `app/routers/status.py`

#### API Endpoints:
```
PUT    /status/product/{product_id} - Update product status
PUT    /status/auction/{auction_id}/result - Update auction result
POST   /status/auction/{auction_id}/finalize - Finalize auction
```

---

### 13. ISSEDatabase - Server-Sent Events
**File**: `app/routers/sse.py`

#### API Endpoints:
```
GET    /sse/notifications          - Stream notifications
GET    /sse/test                   - Test SSE connection
GET    /sse/status                 - Get SSE status
```

---

### 14. IWebSocketDatabase - Real-time WebSocket
**File**: `app/routers/websocket.py`
**Connection Management**: `app/crud.py` (6 functions)

#### API Endpoints:
```
GET    /ws/notifications/{token}   - WebSocket for notifications
GET    /ws/auction/{auction_id}/{token} - WebSocket for auction updates
```

#### WebSocket Functions:
```python
add_connection(user_id: int, websocket: WebSocket)
remove_connection(user_id: int, websocket: WebSocket)
send_to_user(user_id: int, message: dict)
broadcast_to_auction_participants(db: Session, auction_id: int, message: dict)
```

---

## 📊 Thống kê tổng quan

### Database Statistics:
- **Total Interfaces**: 15
- **Total CRUD Functions**: 40+
- **Total API Endpoints**: 89+
- **Real-time Features**: WebSocket + SSE

### Distribution by Domain:
- **Authentication**: 4 CRUD + 11 endpoints
- **Account Management**: 2 CRUD + 2 endpoints
- **Product Management**: 5 CRUD + 5 endpoints
- **Auction Management**: 6 CRUD + 5 endpoints
- **Bidding System**: 6 CRUD + 5 endpoints
- **Payment Management**: 5 CRUD + 5 endpoints
- **Notification System**: 11 functions + 7 endpoints
- **Banking Integration**: 5 endpoints
- **Real-time Features**: 6 WebSocket + 4 SSE endpoints

### Architecture Patterns:
1. **Interface-based Architecture** - 15 distinct database interfaces
2. **CRUD Operations** - Standard Create, Read, Update, Delete patterns
3. **Factory Pattern** - Database factory for interface instantiation
4. **Real-time Communication** - WebSocket + SSE for live updates
5. **Gateway Pattern** - BankPort for external service integration
6. **Repository Pattern** - Centralized CRUD operations in crud.py

---

---

## 🚨 Exception Handling & Error Responses

### Tổng quan Exception Handling
Tất cả API endpoints đều trả về error responses theo format chuẩn. Frontend cần catch và xử lý các exceptions này để đảm bảo user experience tốt.

### 1. HTTP Status Codes

#### 1.1 Success Codes (2xx)
- **200 OK**: Request thành công
- **201 Created**: Tạo resource thành công  
- **204 No Content**: Xóa resource thành công

#### 1.2 Client Error Codes (4xx)
- **400 Bad Request**: Request không hợp lệ
- **401 Unauthorized**: Chưa xác thực hoặc token hết hạn
- **403 Forbidden**: Không có quyền truy cập
- **404 Not Found**: Resource không tồn tại
- **409 Conflict**: Resource đã tồn tại (duplicate)
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded

#### 1.3 Server Error Codes (5xx)
- **500 Internal Server Error**: Lỗi server
- **502 Bad Gateway**: External service error
- **503 Service Unavailable**: Service temporarily down
- **504 Gateway Timeout**: External service timeout

### 2. Standard Error Response Format

#### 2.1 Error Response Structure
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details (optional)",
    "timestamp": "2025-12-08T02:12:02.432Z",
    "path": "/api/endpoint/path"
  }
}
```

#### 2.2 Frontend Error Handling Pattern
```typescript
try {
  const response = await fetch('/api/endpoint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error?.message || 'Unknown error');
  }
  
  return await response.json();
} catch (error) {
  console.error('API Error:', error);
  // Handle error in UI
}
```

### 3. Authentication & Authorization Errors

#### 3.1 Authentication Errors (401)
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password",
    "details": "Authentication failed for user: username@example.com"
  }
}
```

```json
{
  "error": {
    "code": "TOKEN_EXPIRED", 
    "message": "Access token has expired",
    "details": "Please login again"
  }
}
```

```json
{
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Invalid access token",
    "details": "Token format is invalid or corrupted"
  }
}
```

#### 3.2 Authorization Errors (403)
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "User does not have permission to perform this action",
    "details": "Admin privileges required"
  }
}
```

```json
{
  "error": {
    "code": "ACCOUNT_SUSPENDED",
    "message": "Account is suspended",
    "details": "Contact support for assistance"
  }
}
```

### 4. Validation Errors (422)

#### 4.1 Field Validation Errors
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "username": ["Username is required"],
      "email": ["Invalid email format"],
      "password": ["Password must be at least 8 characters"]
    }
  }
}
```

#### 4.2 Business Rule Validation
```json
{
  "error": {
    "code": "AUCTION_NOT_ACTIVE",
    "message": "Auction is not active for bidding",
    "details": "Auction status: COMPLETED, only ACTIVE auctions accept bids"
  }
}
```

```json
{
  "error": {
    "code": "BID_TOO_LOW",
    "message": "Bid amount is too low",
    "details": "Minimum bid: 1000000 VND, current highest: 1500000 VND"
  }
}
```

### 5. Database & System Errors (500)

#### 5.1 Database Connection Errors
```json
{
  "error": {
    "code": "DATABASE_CONNECTION_FAILED",
    "message": "Database connection failed",
    "details": "Unable to connect to MySQL database"
  }
}
```

#### 5.2 Database Schema Errors
```json
{
  "error": {
    "code": "SCHEMA_ERROR",
    "message": "Database schema error",
    "details": "Unknown column 'createdAt' in 'field list'"
  }
}
```

#### 5.3 SQL Integrity Errors
```json
{
  "error": {
    "code": "DUPLICATE_ENTRY",
    "message": "Resource already exists",
    "details": "Username 'john_doe' already exists in database"
  }
}
```

### 6. OTP & Email Service Errors

#### 6.1 OTP Errors
```json
{
  "error": {
    "code": "OTP_EXPIRED",
    "message": "OTP code has expired",
    "details": "OTP expires after 5 minutes, please request a new one"
  }
}
```

```json
{
  "error": {
    "code": "OTP_INVALID",
    "message": "Invalid OTP code",
    "details": "Please check your email and enter the correct 6-digit code"
  }
}
```

#### 6.2 Email Service Errors
```json
{
  "error": {
    "code": "EMAIL_SEND_FAILED",
    "message": "Failed to send email",
    "details": "SMTP server connection timeout"
  }
}
```

```json
{
  "error": {
    "code": "EMAIL_INVALID",
    "message": "Email address is invalid",
    "details": "Unable to deliver to: user@invalid-domain.com"
  }
}
```

### 7. Payment & Banking Errors

#### 7.1 Payment Processing Errors
```json
{
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment processing failed",
    "details": "Insufficient balance in bank account"
  }
}
```

```json
{
  "error": {
    "code": "PAYMENT_TIMEOUT",
    "message": "Payment request timed out",
    "details": "Bank service did not respond within 30 seconds"
  }
}
```

#### 7.2 QR Code Errors
```json
{
  "error": {
    "code": "QR_TOKEN_EXPIRED",
    "message": "QR code has expired",
    "details": "QR token expired at: 2025-12-08T02:30:00Z"
  }
}
```

```json
{
  "error": {
    "code": "QR_TOKEN_USED",
    "message": "QR code has already been used",
    "details": "This payment QR code was already processed"
  }
}
```

### 8. Auction & Bidding Errors

#### 8.1 Auction State Errors
```json
{
  "error": {
    "code": "AUCTION_NOT_FOUND",
    "message": "Auction not found",
    "details": "Auction ID: 123 does not exist"
  }
}
```

```json
{
  "error": {
    "code": "AUCTION_ALREADY_ENDED",
    "message": "Auction has already ended",
    "details": "Auction end date: 2025-12-07T18:00:00Z"
  }
}
```

#### 8.2 Bidding Errors
```json
{
  "error": {
    "code": "BID_ALREADY_PLACED",
    "message": "User has already placed a bid",
    "details": "Only one bid per user is allowed per auction"
  }
}
```

```json
{
  "error": {
    "code": "BID_CANCEL_NOT_ALLOWED",
    "message": "Bid cannot be cancelled",
    "details": "Bids can only be cancelled if auction has not started"
  }
}
```

### 9. File Upload & Image Errors

#### 9.1 Image Upload Errors
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds limit",
    "details": "Maximum file size: 5MB, received: 8.5MB"
  }
}
```

```json
{
  "error": {
    "code": "INVALID_IMAGE_FORMAT",
    "message": "Invalid image format",
    "details": "Supported formats: JPG, PNG, WEBP"
  }
}
```

```json
{
  "error": {
    "code": "UPLOAD_FAILED",
    "message": "File upload failed",
    "details": "Unable to save file to storage system"
  }
}
```

### 10. Real-time Communication Errors

#### 10.1 WebSocket Errors
```json
{
  "error": {
    "code": "WEBSOCKET_CONNECTION_FAILED",
    "message": "WebSocket connection failed",
    "details": "Unable to establish real-time connection"
  }
}
```

#### 10.2 SSE Errors
```json
{
  "error": {
    "code": "SSE_CONNECTION_LOST",
    "message": "Server-Sent Events connection lost",
    "details": "Connection was closed by server"
  }
}
```

### 11. Rate Limiting Errors (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": "Rate limit: 100 requests per hour, try again later"
  }
}
```

### 12. Frontend Exception Handling Best Practices

#### 12.1 Global Error Handler
```typescript
class ApiErrorHandler {
  static handle(error: any): void {
    const errorCode = error.error?.code;
    const message = error.error?.message;
    
    switch (errorCode) {
      case 'TOKEN_EXPIRED':
      case 'TOKEN_INVALID':
        // Redirect to login
        window.location.href = '/login';
        break;
        
      case 'INSUFFICIENT_PERMISSIONS':
        // Show access denied message
        this.showError('You do not have permission to perform this action');
        break;
        
      case 'VALIDATION_ERROR':
        // Show field-specific errors
        this.showValidationErrors(error.error.details);
        break;
        
      case 'DATABASE_CONNECTION_FAILED':
        // Show system error message
        this.showError('System is temporarily unavailable. Please try again later.');
        break;
        
      default:
        // Generic error handling
        this.showError(message || 'An unexpected error occurred');
    }
  }
  
  private static showError(message: string): void {
    // Implement your UI error display logic
    console.error('API Error:', message);
  }
  
  private static showValidationErrors(details: any): void {
    // Implement field-specific error display
    console.error('Validation Errors:', details);
  }
}
```

#### 12.2 Retry Logic for Transient Errors
```typescript
async function apiCallWithRetry(apiCall: () => Promise<any>, maxRetries = 3): Promise<any> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      const errorCode = error.error?.code;
      
      // Retry for transient errors only
      if (['DATABASE_CONNECTION_FAILED', 'PAYMENT_TIMEOUT', 'EMAIL_SEND_FAILED'].includes(errorCode) && i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // Exponential backoff
        continue;
      }
      
      // Don't retry for client errors or permanent failures
      throw error;
    }
  }
}
```

#### 12.3 Loading States & User Feedback
```typescript
// Show loading state
setLoading(true);

try {
  const result = await apiCallWithRetry(() => fetch('/api/endpoint'));
  setData(result);
} catch (error) {
  ApiErrorHandler.handle(error);
} finally {
  setLoading(false);
}
```

### 13. Critical Errors That Require Immediate Attention

#### 13.1 Database Connection Issues
```json
{
  "error": {
    "code": "CRITICAL_DATABASE_ERROR",
    "message": "Critical database error - system may be unstable",
    "details": "Connection pool exhausted, unable to serve requests"
  }
}
```

#### 13.2 External Service Failures
```json
{
  "error": {
    "code": "BANK_SERVICE_DOWN",
    "message": "Banking service is temporarily unavailable",
    "details": "All payment operations are suspended until service is restored"
  }
}
```

### 14. Error Logging & Monitoring

#### 14.1 Client-side Error Logging
```typescript
function logError(error: any, context: string): void {
  console.error(`[${context}] Error:`, {
    code: error.error?.code,
    message: error.error?.message,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    userAgent: navigator.userAgent
  });
  
  // Send to monitoring service
  // monitoringService.logError(error, context);
}
```

---

## Cập nhật cuối cùng
- **Ngày**: 2025-12-08
- **Phiên bản**: v2.6
- **Người cập nhật**: Kilo Code
- **Ghi chú**: 
  - Thêm comprehensive exception handling documentation
  - Thêm error response formats và HTTP status codes
  - Thêm frontend exception handling patterns và best practices
  - Thêm critical error categories và retry logic
- **Files cập nhật**:
  - `API_ENDPOINTS_GUIDE.md` - Thêm Exception Handling & Error Responses section

