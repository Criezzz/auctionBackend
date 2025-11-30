# API Endpoints Guide Sync Report

## 📊 Executive Summary

Kiểm tra so sánh `API_ENDPOINTS_GUIDE.md` (version 2.3) với codebase hiện tại, phát hiện **6 inconsistencies cần sync**:

- ❌ **2 Critical**: Password recovery flow mismatch
- ⚠️ **2 Important**: OTP response format differences  
- ℹ️ **2 Minor**: Missing/extra endpoints

## 🚨 CRITICAL ISSUES - Cần Sync Ngay

### 1. Password Recovery Flow Mismatch

**API Guide v2.3**:
```
POST /auth/recover         # Request OTP for password recovery
POST /auth/recover/verify  # Verify OTP → get reset_token  
POST /auth/reset          # Use reset_token to set new password
```

**Current Implementation**:
```javascript
// src/features/auth/password.js
POST /auth/reset/request   # Uses different endpoint name
POST /auth/reset/confirm   # Uses different endpoint name
```

**Impact**: ❌ **CRITICAL** - Password recovery sẽ fail khi connect với backend v2.3
**Action Required**: Update `src/features/auth/password.js` endpoints

### 2. Rate Limiting Conflicts

**API Guide v2.3**:
- Line 97-98: OTP verify response có `remaining_trials`
- Line 104: Failed OTP response có `remaining_trials` và `updated_token`

**Current Implementation**:
```javascript
// src/features/auth/mockRepo.js - Line 165-169
if (otp_code !== otpData.otp_code) {
  return {
    success: false,
    message: 'Mã OTP không đúng.'  // Không có remaining_trials
  }
}
```

**Impact**: ⚠️ **IMPORTANT** - Frontend expect `remaining_trials` nhưng không có, có thể break UI
**Action Required**: Remove remaining_trials references hoặc add mock implementation

## ⚠️ IMPORTANT ISSUES - Cần Sync

### 3. OTP Response Format Inconsistencies

**API Guide v2.3** - Successful OTP verify:
```json
{
  "success": true,
  "message": "Xác minh email thành công! Tài khoản đã được kích hoạt.",
  "remaining_trials": 5  // <-- This field exists in guide
}
```

**Current Implementation**:
```javascript
// src/features/auth/mockRepo.js - Line 181-184
return {
  success: true,
  message: 'Xác minh email thành công! Tài khoản đã được kích hoạt.'
  // Không có remaining_trials
}
```

### 4. Resend OTP Endpoint Auth Header

**API Guide v2.3**:
- Line 127: Rate limit 3 requests/15min per IP
- Line 110-127: POST `/auth/register/resend` - **No authentication required**

**Current Implementation**:
```javascript
// src/features/auth/register.js - Line 69-82
return httpPost('/auth/register/resend', 
  { username: username.trim() },
  {
    headers: {
      'Authorization': `Bearer ${otpToken}`  // <-- Adding auth header
    }
  }
)
```

**Impact**: ⚠️ **IMPORTANT** - May cause 422 error như đã fix trong guide
**Action Required**: Remove Authorization header từ resend OTP

## ℹ️ MINOR ISSUES - Optional Sync

### 5. Admin API Endpoint Differences

**API Guide v2.3**:
```javascript
PUT /status/product/{product_id}        // Update shipping status
PUT /status/auction/{id}/result         // Update auction result
POST /status/auction/{id}/finalize      // Finalize auction
```

**Current Implementation**:
```javascript
// src/features/admin/api.js
POST `/admin/products/${productId}/status`    // Different path
POST `/admin/auctions/${auctionId}/result`    // Different path  
// Missing: /status/* endpoints
```

### 6. Mock Bank API Status

**API Guide v2.3**: 
- Lists complete `/bank/*` endpoints (Lines 1013-1218)

**Handoff Brief**: 
- States these are "DEPRECATED in v2.1" (Lines 381-389)

**Current Status**: 
- Still using `GET /bank/terms` trong TermsOfServiceModal
- Other bank endpoints not used

## 📋 RECOMMENDED ACTIONS

### Priority 1 - Critical (Must Fix)

1. **Update Password Recovery Endpoints**
   ```javascript
   // src/features/auth/password.js
   // Change from:
   POST /auth/reset/request
   POST /auth/reset/confirm
   
   // To:
   POST /auth/recover
   POST /auth/recover/verify  
   POST /auth/reset
   ```

2. **Remove OTP Rate Limiting References**
   ```javascript
   // Remove remaining_trials từ:
   // - mockRepo.js verifyOTP response
   // - UI components expecting remaining_trials
   ```

### Priority 2 - Important (Should Fix)

3. **Fix Resend OTP Auth Header**
   ```javascript
   // src/features/auth/register.js - Remove Authorization header
   return httpPost('/auth/register/resend', { username: username.trim() })
   ```

4. **Standardize Admin API Paths**
   ```javascript
   // Consider aligning với API guide structure
   PUT /status/product/{id} thay vì POST /admin/products/{id}/status
   ```

### Priority 3 - Optional (Nice to Have)

5. **Update Terms of Service Integration**
   - Consider if `/bank/terms` should be replaced
   - Or update API guide để reflect deprecation status

6. **Document Version Alignment**
   - Update API guide version number if changes made
   - Update handoff brief để reflect current status

## ✅ ALREADY ALIGNED - No Action Needed

### Authentication Flow ✅
- OTP registration: `/auth/register` ✅
- OTP verification: `/auth/register/verify` ✅  
- OTP resend: `/auth/register/resend` ✅
- Login/refresh: `/auth/login`, `/auth/refresh` ✅
- User profile: `/auth/me` ✅

### Auction & Payment Flow ✅
- Participation: `/participation/register` ✅
- Bidding: `/bids/place` ✅
- Payment: `/payments/create` ✅
- QR payment: `/payments/qr-callback/{token}` ✅

### Real-time Features ✅
- WebSocket: `/ws/notifications/{token}` ✅
- SSE: `/sse/notifications` ✅

## 🎯 CONCLUSION

**Most Critical**: Password recovery endpoint mismatch sẽ break functionality khi connect với backend v2.3

**Status**: Frontend codebase mostly aligned với API v2.3, chỉ cần small fixes for consistency

**Next Steps**: 
1. Fix password recovery endpoints immediately
2. Remove rate limiting references  
3. Test với backend v2.3 when available

---

## 🎯 NEW FEATURE: Local File Upload Implementation

### ✅ COMPLETED: File Selection for Image Uploads

**Thêm chức năng chọn file từ máy thay vì nhập URL ảnh:**

#### 1. **Updated API Functions** (src/features/user/api.js)
- ✅ `submitProductWithImages()` - Upload product với ảnh
- ✅ `uploadImage()` - Upload single image  
- ✅ `uploadMultipleImages()` - Upload multiple images
- ✅ Sử dụng multipart/form-data với local disk storage

#### 2. **Updated SubmitProductPage** (src/pages/SubmitProductPage.jsx)
- ✅ Thay thế `image_url` input với file selection
- ✅ Hỗ trợ upload ảnh chính + 4 ảnh phụ tối đa
- ✅ File preview và drag-drop interface
- ✅ File validation (5MB limit, JPEG/PNG/WebP support)
- ✅ Real-time image preview với remove functionality

#### 3. **Updated AdminCreateAuctionPage** (src/pages/AdminCreateAuctionPage.jsx)  
- ✅ Converted to 2-step process: Product → Auction
- ✅ Step 1: Tạo product với image uploads (same as SubmitProductPage)
- ✅ Step 2: Tạo auction cho product đã được tạo
- ✅ Follows correct API flow: `/products/register-with-images` → `/auctions/register`

#### 4. **Enhanced CSS** (src/index.css)
- ✅ Added `btn-secondary` class for better UI
- ✅ File upload styling với drag-drop zones

### 🎯 File Upload Features:
- **Support Formats**: JPEG, PNG, WebP (auto-converted to JPEG)
- **File Size Limit**: 5MB per file  
- **Image Count**: 1 main image + up to 4 additional images
- **Storage**: Local disk on backend (`storage/images/products/`)
- **API Integration**: Uses `/products/register-with-images` endpoint
- **Preview**: Real-time image preview với remove capability
- **Validation**: Client-side file validation trước upload

### 📋 Backend API Integration:
```javascript
// Product với Images
POST /products/register-with-images
Content-Type: multipart/form-data

// Individual Image Upload  
POST /images/upload
POST /images/upload/multiple
```

---

## 🚀 UPDATE: Live Server Configuration Complete

**Frontend đã được cấu hình sử dụng live backend server:**

### ✅ Completed Actions:
1. **Environment Configuration**: 
   - `.env` đã có `VITE_API_BASE_URL=http://localhost:8000`
   - Logic `useMock = !apiBase()` sẽ tự động dùng real API
   
2. **Enhanced Environment Variables**:
   - Bổ sung SMTP configuration vào `.env.example`
   - Thêm JWT, Database, và Bank API configs

3. **Testing Tools Created**:
   - `test_backend_connection.js` - Automated backend test
   - `otp_manual_test.js` - Manual OTP testing script
   - Updated `OTP_TESTING_GUIDE.md` cho live server

### 🎯 Current Status:
- **Mode**: Live backend server (không còn mock)
- **OTP**: Real email sending via SMTP
- **Connection**: Automatic với `http://localhost:8000`
- **Testing**: Ready với provided test scripts

### 📋 Next Steps for User:
```bash
# Test backend connection
node test_backend_connection.js

# Manual OTP test  
node otp_manual_test.js username email

# Or use curl directly
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test123","email":"test@test.com","password":"pass123","first_name":"Test","last_name":"User","phone_num":"+84123456789"}'
```

---

**Generated**: 2025-11-29T14:11:06Z  
**Updated**: 2025-11-29T14:11:06Z  
**API Guide Version**: 2.3  
**Codebase Status**: ✅ LIVE SERVER MODE - Ready for Production Testing