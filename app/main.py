from fastapi import FastAPI, Depends, HTTPException, WebSocket, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from . import crud, models, schemas
from .database import SessionLocal, engine
from .routers import auth, accounts, products, auctions, search, participation, bids, payments, status, websocket, sse, notifications, bank
from .config import settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Auction Backend API",
    description="Backend for online auction platform with email verification, OTP authentication, and comprehensive functionality",
    version="2.0.0",
    contact={
        "name": "Auction API Support",
        "email": "support@auction.com",
    },
)

# Trusted Host middleware for security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*.example.com"]
)

# CORS middleware for frontend integration
allowed_origins = [
    "http://localhost:3000",    # React dev server
    "http://localhost:5173",    # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
    # Note: Never use "*" when allow_credentials=True
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    """Handle validation errors"""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "detail": "Validation failed",
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include routers (routers already have their own prefix defined)
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(products.router)
app.include_router(auctions.router)
app.include_router(search.router)
app.include_router(participation.router)
app.include_router(bids.router)
app.include_router(payments.router)
app.include_router(status.router)
app.include_router(websocket.router)
app.include_router(sse.router)
app.include_router(notifications.router)
app.include_router(bank.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create database tables
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown"""
    # Clean up WebSocket connections
    crud.active_connections.clear()
    print("WebSocket connections cleaned up")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Auction Backend API v2.0",
        "version": "2.0.0",
        "description": "Comprehensive auction platform backend with email verification, OTP authentication, password recovery, and real-time notifications",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "new_features_v2": {
            "email_verification": "OTP-based email verification during registration",
            "password_recovery": "OTP-based password recovery system",
            "otp_management": "Secure OTP tokens stored in client localStorage",
            "rate_limiting": "Simple in-memory rate limiting for security",
            "enhanced_security": "Password strength validation and input sanitization"
        },
        "endpoints": {
            "Authentication": {
                "base": "/auth",
                "endpoints": [
                    "POST /auth/register - Register with OTP email verification",
                    "POST /auth/register/verify - Verify OTP for registration", 
                    "POST /auth/register/resend - Resend OTP for registration",
                    "POST /auth/login - User login",
                    "POST /auth/refresh - Refresh access token",
                    "POST /auth/recover - Request password recovery OTP",
                    "POST /auth/recover/verify - Verify recovery OTP",
                    "POST /auth/reset - Reset password with reset token",
                    "POST /auth/logout - User logout",
                    "GET /auth/me - Get current user info",
                    "GET /auth/otp/status - Get OTP token status"
                ]
            },
            "Account Management": "/accounts/*",
            "Product Management": "/products/*", 
            "Auction Management": "/auctions/*",
            "Search & Filter": "/search/*",
            "Participation": "/participation/*",
            "Bidding": "/bids/*",
            "Payments": "/payments/*",
            "Mock Bank API": "/bank/*",
            "Status Management": "/status/*",
            "WebSocket": "/ws/*",
            "Server-Sent Events": "/sse/*",
            "Notifications": "/notifications/*"
        },
        "authentication_flow": {
            "registration": [
                "1. POST /auth/register - Create account, send OTP email",
                "2. Store otp_token in localStorage",
                "3. POST /auth/register/verify - Verify OTP code",
                "4. Account activated, tokens returned for auto-login"
            ],
            "password_recovery": [
                "1. POST /auth/recover - Request OTP for password recovery",
                "2. Store otp_token in localStorage", 
                "3. POST /auth/recover/verify - Verify OTP, receive reset_token",
                "4. POST /auth/reset - Use reset_token to set new password"
            ]
        },
        "security_features": {
            "rate_limiting": {
                "registration": "3 attempts/hour per IP",
                "login": "5 attempts/15min per IP",
                "otp_resend": "3 requests/15min per IP",
                "password_recovery": "3 requests/15min per IP"
            },
            "password_requirements": {
                "min_length": "8 characters",
                "required": ["uppercase", "lowercase", "number", "special character"]
            },
            "otp_settings": {
                "length": "6 digits",
                "expiry": "5 minutes",
                "max_trials": 5
            }
        },
        "real_time_features": {
            "WebSocket": {
                "notifications": "ws://localhost:8000/ws/notifications/{access_token}",
                "auction_updates": "ws://localhost:8000/ws/auction/{auction_id}/{access_token}"
            },
            "SSE": {
                "notifications": "GET /sse/notifications (with Authorization header)",
                "auction_updates": "GET /sse/auction/{auction_id} (with Authorization header)",
                "test": "GET /sse/test (with Authorization header)"
            },
            "notification_types": [
                "bid_outbid - When user is outbid",
                "bid_placed - Confirmation of bid placement",
                "auction_ending - Warning before auction ends",
                "auction_won - When user wins an auction",
                "payment_required - When payment is needed"
            ]
        },
        "email_templates": {
            "otp_verification": "Beautiful HTML email with OTP code",
            "welcome_email": "Welcome message after successful registration",
            "responsive_design": "Mobile-friendly email templates"
        },
        "docs": "/docs",
        "openapi_spec": "/openapi.json",
        "health_check": "/health"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "email_service": "configured",
            "otp_service": "active",
            "rate_limiting": "enabled"
        }
    }


