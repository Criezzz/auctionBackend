"""
Application configuration loaded from environment variables
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/auction_db"
    
    # JWT Authentication
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OTP and Password Reset Token Keys (separate from main SECRET_KEY)
    SECRET_OTP_KEY: str = "dev-otp-secret-change-in-production"
    SECRET_RESET_KEY: str = "dev-reset-secret-change-in-production"
    
    # Token Expiration Times
    OTP_TOKEN_EXPIRE_MINUTES: int = 5
    RESET_TOKEN_EXPIRE_MINUTES: int = 5
    OTP_MAX_TRIALS: int = 5
    
    # Payment Token Keys (separate from other tokens)
    SECRET_PAYMENT_TOKEN_KEY: str = "dev-payment-secret-change-in-production"
    
    # Payment Token Expiration Times
    DEPOSIT_TOKEN_EXPIRE_MINUTES: int = 5
    PAYMENT_TOKEN_EXPIRE_HOURS: int = 24
    
    # Application
    DEBUG: bool = True
    APP_NAME: str = "Auction Backend API"
    APP_VERSION: str = "1.0.0"
    APP_URL: str = "http://localhost:8000"
    
    # CORS (optional, for frontend integration)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

