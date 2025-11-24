"""
Authentication endpoints: login, refresh, me, OTP verification, password recovery
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import asyncio

from .. import crud, schemas
from ..database import SessionLocal
from ..auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    create_otp,
    verify_otp,
    create_reset_token,
    verify_reset_token,
    validate_password_strength,
    validate_email_format,
    validate_username_format,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from ..utils.mailer import send_otp_email, send_welcome_email
from ..utils.otp_manager import get_token_status, decode_otp_token
from ..utils.rate_limiter import check_client_ip_rate_limit, check_username_rate_limit, reset_rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dependency to get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = crud.get_account_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    login_data: schemas.LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint: authenticate user and return JWT tokens
    
    POST /auth/login
    Body: { "username": "user123", "password": "secret" }
    Returns: { "access_token", "refresh_token", "token_type", "expires_in" }
    
    Rate Limit: 5 attempts per 15 minutes
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not check_client_ip_rate_limit(client_ip, "login", 5, 15):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again after 15 minutes."
        )
    
    # Authenticate user
    user = crud.authenticate_account(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated",
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # convert to seconds
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    refresh_data: schemas.RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh token endpoint: get new access token using refresh token
    
    POST /auth/refresh
    Body: { "refresh_token": "..." }
    Returns: { "access_token", "refresh_token", "token_type", "expires_in" }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log incoming request (without token for security)
    logger.info("Refresh token request received")
    
    # Verify refresh token
    try:
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload is None:
        logger.warning("Refresh token verification failed - invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        logger.warning("Refresh token missing username in payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Verify user still exists
    user = crud.get_account_by_username(db, username)
    if not user:
        logger.warning(f"User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.activated:
        logger.warning(f"User not activated: {username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated",
        )
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.account_id}
    )
    
    logger.info(f"New tokens generated for user: {username}")
    
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user = Depends(get_current_user)):
    """
    Get current user info endpoint
    
    GET /auth/me
    Headers: Authorization: Bearer <access_token>
    Returns: { "id", "username", "email", "role", ... }
    """
    return schemas.UserResponse(
        id=current_user.account_id,
        username=current_user.username,
        email=current_user.email,
        role="admin" if current_user.is_admin else "user",
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone_num=current_user.phone_num,
        date_of_birth=current_user.date_of_birth,
        activated=current_user.activated,
        is_authenticated=current_user.is_authenticated,
        created_at=current_user.created_at
    )


# ========== NEW OTP & PASSWORD RECOVERY ENDPOINTS ========== #

@router.post("/register", response_model=schemas.RegistrationWithOTPResponse)
async def register_with_otp(
    account_data: schemas.AccountCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register new account with OTP email verification
    
    POST /auth/register
    Body: AccountCreate data
    Returns: RegistrationWithOTPResponse with otp_token
    
    Rate Limit: 3 registrations per hour per IP
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Validate input
    username_validation = validate_username_format(account_data.username)
    if not username_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=username_validation["message"]
        )
    
    if not validate_email_format(account_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Địa chỉ email không hợp lệ"
        )
    
    password_validation = validate_password_strength(account_data.password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu không đủ mạnh: " + "; ".join(password_validation["errors"])
        )
    
    # Check if username already exists
    existing_user = crud.get_account_by_username(db, account_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username đã tồn tại"
        )
    
    # Check if email already exists
    existing_email = db.query(crud.models.Account).filter(
        crud.models.Account.email == account_data.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã tồn tại"
        )
    
    # Create account (activated=false by default)
    account_data_dict = account_data.dict()
    account_data_dict["activated"] = False
    account_data_dict["is_authenticated"] = False
    
    # Note: Password will be hashed in crud.create_account, so don't hash it here
    
    db_account = crud.create_account(db=db, account=schemas.AccountCreate(**account_data_dict))
    
    # Generate OTP
    otp_data = create_otp(account_data.username, "registration", db)
    
    # Send OTP email (temporarily disabled for testing)
    try:
        email_sent = await send_otp_email(
            otp=otp_data["otp_code"],
            username=account_data.username,
            target_address=account_data.email,
            request_type="registration"
        )
    except Exception as e:
        print(f"Email sending failed (non-fatal): {e}")
        email_sent = False
    
    # Don't fail registration if email fails (for testing)
    # if not email_sent:
    #     db.delete(db_account)
    #     db.commit()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Không thể gửi email xác minh. Vui lòng thử lại sau."
    #     )
    
    return schemas.RegistrationWithOTPResponse(
        success=True,
        message="Tài khoản đã được tạo. Vui lòng kiểm tra email để xác minh OTP.",
        otp_token=otp_data["otp_token"],
        expires_in=5 * 60,  # 5 minutes
        user=schemas.UserResponse(
            id=db_account.account_id,
            username=db_account.username,
            email=db_account.email,
            role="user",
            first_name=db_account.first_name,
            last_name=db_account.last_name,
            phone_num=db_account.phone_num,
            date_of_birth=db_account.date_of_birth,
            activated=db_account.activated,
            is_authenticated=db_account.is_authenticated,
            created_at=db_account.created_at
        )
    )


@router.post("/register/verify", response_model=schemas.OTPVerificationResponse)
async def verify_registration_otp(
    verify_data: schemas.OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code for registration
    
    POST /auth/register/verify
    Body: { "otp_code": "123456", "otp_token": "jwt_token", "username": "user123" }
    Returns: OTPVerificationResponse
    """
    # Verify OTP
    otp_result = verify_otp(verify_data.otp_code, verify_data.otp_token, verify_data.username, "registration")
    
    if otp_result["success"]:
        # OTP is correct, activate account
        user = crud.get_account_by_username(db, verify_data.username)
        if user:
            user.activated = True
            user.is_authenticated = True
            db.commit()
            
            # Send welcome email
            await send_welcome_email(user.username, user.email)
            
            # Create tokens for auto-login
            access_token = create_access_token(
                data={"sub": user.username, "user_id": user.account_id}
            )
            refresh_token = create_refresh_token(
                data={"sub": user.username, "user_id": user.account_id}
            )
            
            return schemas.OTPVerificationResponse(
                success=True,
                message="Xác minh email thành công! Tài khoản đã được kích hoạt.",
                remaining_trials=otp_result["remaining_trials"],
                updated_token=None
            )
        else:
            return schemas.OTPVerificationResponse(
                success=False,
                message="Không tìm thấy người dùng"
            )
    else:
        return schemas.OTPVerificationResponse(
            success=False,
            message=otp_result["message"],
            remaining_trials=otp_result["remaining_trials"],
            updated_token=otp_result.get("updated_token")
        )


@router.post("/register/cancel", response_model=schemas.MessageResponse)
async def cancel_registration(
    cancel_data: schemas.RegistrationCancelRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel registration and delete unactivated account
    
    POST /auth/register/cancel
    Body: { "username": "newuser123" }
    Returns: { "success": true, "message": "Tài khoản chưa kích hoạt đã được xóa thành công" }
    
    Restrictions:
    - Can only delete unactivated accounts (activated=false)
    - Account must not have any active bids or participation
    """
    
    # Get user
    user = crud.get_account_by_username(db, cancel_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản"
        )
    
    # Check if account is already activated
    if user.activated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa tài khoản đã được kích hoạt"
        )
    
    # Check if user has any active participation in auctions
    active_participations = db.query(models.Payment).filter(
        models.Payment.user_id == user.account_id,
        models.Payment.payment_status.in_(["pending", "completed"])
    ).count()
    
    if active_participations > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa tài khoản đã tham gia đấu giá"
        )
    
    # Check if user has any active bids
    active_bids = db.query(models.Bid).filter(
        models.Bid.user_id == user.account_id,
        models.Bid.bid_status == "active"
    ).count()
    
    if active_bids > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa tài khoản đã đặt giá thầu"
        )
    
    # Delete the unactivated account
    success = crud.delete_unactivated_account(db, cancel_data.username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xóa tài khoản"
        )
    
    return schemas.MessageResponse(
        success=True,
        message="Tài khoản chưa kích hoạt đã được xóa thành công"
    )


@router.post("/register/resend", response_model=schemas.OTPResendResponse)
async def resend_registration_otp(
    resend_data: schemas.OTPRegistrationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Resend OTP for registration
    
    POST /auth/register/resend
    Body: { "username": "user123" }
    Headers: Authorization: Bearer <access_token>
    Returns: OTPResendResponse
    
    Rate Limit: 3 resend requests per 15 minutes
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not check_client_ip_rate_limit(client_ip, "otp_resend", 3, 15):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quá nhiều yêu cầu gửi lại OTP. Vui lòng thử lại sau 15 phút."
        )
    
    # Get user
    user = crud.get_account_by_username(db, resend_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng"
        )
    
    # Check if already activated
    if user.activated:
        return schemas.OTPResendResponse(
            success=False,
            message="Tài khoản đã được kích hoạt"
        )
    
    # Generate new OTP
    otp_data = create_otp(user.username, "registration", db)
    
    # Send OTP email
    email_sent = await send_otp_email(
        otp=otp_data["otp_code"],
        username=user.username,
        target_address=user.email,
        request_type="registration"
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể gửi email. Vui lòng thử lại sau."
        )
    
    return schemas.OTPResendResponse(
        success=True,
        message="OTP mới đã được gửi đến email của bạn",
        otp_token=otp_data["otp_token"],
        expires_in=5 * 60  # 5 minutes
    )


@router.post("/recover", response_model=schemas.PasswordRecoveryResponse)
async def request_password_recovery(
    recovery_data: schemas.PasswordRecoveryRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password recovery OTP
    
    POST /auth/recover
    Body: { "username": "user123" }
    Returns: PasswordRecoveryResponse
    
    Rate Limit: 3 recovery requests per 15 minutes per IP
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not check_client_ip_rate_limit(client_ip, "password_recover", 3, 15):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quá nhiều yêu cầu khôi phục mật khẩu. Vui lòng thử lại sau 15 phút."
        )
    
    # Get user by username or email
    user = crud.get_account_by_username(db, recovery_data.username)
    if not user:
        # Don't reveal if user exists or not
        return schemas.PasswordRecoveryResponse(
            success=True,
            message="Nếu tài khoản tồn tại, OTP sẽ được gửi đến email của bạn"
        )
    
    # Generate OTP
    otp_data = create_otp(user.username, "password_reset", db)
    
    # Send OTP email
    email_sent = await send_otp_email(
        otp=otp_data["otp_code"],
        username=user.username,
        target_address=user.email,
        request_type="password_reset"
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể gửi email. Vui lòng thử lại sau."
        )
    
    return schemas.PasswordRecoveryResponse(
        success=True,
        message="OTP khôi phục mật khẩu đã được gửi đến email của bạn",
        otp_token=otp_data["otp_token"],
        expires_in=5 * 60  # 5 minutes
    )


@router.post("/recover/verify", response_model=schemas.ResetTokenResponse)
async def verify_password_recovery_otp(
    verify_data: schemas.OTPVerifyPasswordRecoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP for password recovery and get reset token
    
    POST /auth/recover/verify
    Body: { "otp_code": "123456", "otp_token": "jwt_token", "username": "user123" }
    Returns: ResetTokenResponse
    """
    # Verify OTP
    otp_result = verify_otp(verify_data.otp_code, verify_data.otp_token, verify_data.username, "password_reset")
    
    if otp_result["success"]:
        # OTP is correct, create reset token
        reset_token = create_reset_token(verify_data.username)
        
        return schemas.ResetTokenResponse(
            success=True,
            message="Xác minh OTP thành công. Bạn có thể đặt lại mật khẩu.",
            reset_token=reset_token,
            expires_in=5 * 60  # 5 minutes
        )
    else:
        return schemas.ResetTokenResponse(
            success=False,
            message=otp_result["message"],
            reset_token=None,
            expires_in=None
        )


@router.post("/reset", response_model=schemas.PasswordResetResponse)
async def reset_password(
    reset_data: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token
    
    POST /auth/reset
    Body: { "reset_token": "jwt_token", "new_password": "newpassword123" }
    Returns: PasswordResetResponse
    """
    # Verify reset token
    token_payload = verify_reset_token(reset_data.reset_token)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token khôi phục không hợp lệ hoặc đã hết hạn"
        )
    
    # Validate new password
    password_validation = validate_password_strength(reset_data.new_password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới không đủ mạnh: " + "; ".join(password_validation["errors"])
        )
    
    # Get user
    username = token_payload["sub"]
    user = crud.get_account_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng"
        )
    
    # Hash new password
    user.password = get_password_hash(reset_data.new_password)
    db.commit()
    
    return schemas.PasswordResetResponse(
        success=True,
        message="Mật khẩu đã được đặt lại thành công"
    )


@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout endpoint - invalidate access token
    
    POST /auth/logout
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # In a more complex implementation, you might want to:
    # 1. Add the token to a blacklist
    # 2. Track logout time
    # 3. Invalidate refresh tokens
    
    # For now, just return success
    # The frontend should remove tokens from storage
    return {"message": "Đăng xuất thành công", "success": True}


@router.get("/otp/status", response_model=schemas.OTPStatusResponse)
async def get_otp_status(otp_token: str):
    """
    Get OTP token status without verifying OTP code
    
    GET /auth/otp/status?otp_token=jwt_token
    Returns: OTPStatusResponse
    """
    status_info = get_token_status(otp_token)
    
    return schemas.OTPStatusResponse(
        valid=status_info["valid"],
        expired=status_info["expired"],
        remaining_trials=status_info["remaining_trials"],
        purpose=status_info["purpose"],
        username=status_info["username"],
        expires_at=status_info["expires_at"],
        message="OTP token hợp lệ" if status_info["valid"] else "OTP token không hợp lệ hoặc đã hết hạn"
    )


@router.post("/debug/verify-token")
async def debug_verify_token(token_data: dict):
    """
    Debug endpoint to verify token structure
    
    POST /auth/debug/verify-token
    Body: { "token": "your_token_here", "token_type": "access" or "refresh" }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    token = token_data.get("token")
    token_type = token_data.get("token_type", "access")
    
    if not token:
        return {"error": "No token provided"}
    
    try:
        payload = verify_token(token, token_type=token_type)
        
        if payload:
            return {
                "valid": True,
                "payload": payload,
                "message": f"Token is valid {token_type} token"
            }
        else:
            return {
                "valid": False,
                "message": f"Token verification failed - invalid or wrong type (expected {token_type})"
            }
    except Exception as e:
        logger.error(f"Token debug error: {str(e)}")
        return {
            "valid": False,
            "error": str(e),
            "message": "Token parsing error"
        }

