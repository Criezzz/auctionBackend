# Auction Backend - FastAPI + SQLAlchemy

Backend API cho sàn đấu giá online với JWT authentication.

## Quick Start (PowerShell)

```powershell
# Tạo virtual environment và cài packages
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Chạy server
uvicorn app.main:app --reload

# Server chạy tại: http://127.0.0.1:8000
# API docs: http://127.0.0.1:8000/docs
```

## Authentication Endpoints

### POST /auth/login
Đăng nhập và nhận JWT tokens.

```json
Request:
{
  "username": "user123",
  "password": "secret"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/refresh
Làm mới access token bằng refresh token.

```json
Request:
{
  "refresh_token": "eyJ..."
}

Response: (same as login)
```

### GET /auth/me
Lấy thông tin user hiện tại (cần access token).

```
Headers: Authorization: Bearer <access_token>

Response:
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "role": "user",
  "first_name": "John",
  "last_name": "Doe",
  ...
}
```

## Project Structure

- `app/main.py` - FastAPI application & routes
- `app/database.py` - SQLAlchemy config
- `app/models.py` - Database models (Account, Auction, Bid, Product, Payment)
- `app/schemas.py` - Pydantic schemas
- `app/crud.py` - Database operations
- `app/auth.py` - JWT utilities & password hashing
- `app/routers/auth.py` - Authentication endpoints

## Testing với curl/PowerShell

```powershell
# Login
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" `
  -Method Post -ContentType "application/json" `
  -Body '{"username":"admin","password":"test123"}'

# Lưu token
$token = $response.access_token

# Get user info
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/me" `
  -Headers @{Authorization="Bearer $token"}
```

