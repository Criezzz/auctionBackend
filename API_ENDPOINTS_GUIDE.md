# API Endpoints Guide - Auction System

## Tổng quan
Đây là hướng dẫn đầy đủ về các API endpoints và Gateway classes trong Auction System.

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

## Cập nhật cuối cùng
- **Ngày**: 2024-11-30
- **Phiên bản**: v1.0
- **Người cập nhật**: Kilo Code
- **Ghi chú**: Hoàn thành refactoring BankPort và EmailPort gateway classes

