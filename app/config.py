"""
Application configuration loaded from environment variables
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    # OTP and Password Reset Token Keys (separate from main SECRET_KEY)
    SECRET_OTP_KEY: str
    SECRET_RESET_KEY: str
    
    # Token Expiration Times
    OTP_TOKEN_EXPIRE_MINUTES: int
    RESET_TOKEN_EXPIRE_MINUTES: int
    OTP_MAX_TRIALS: int
    
    # Payment Token Keys (separate from other tokens)
    SECRET_PAYMENT_TOKEN_KEY: str
    
    # Payment Token Expiration Times
    DEPOSIT_TOKEN_EXPIRE_MINUTES: int
    PAYMENT_TOKEN_EXPIRE_HOURS: int
    
    # Application
    DEBUG: bool
    APP_NAME: str
    APP_VERSION: str
    APP_URL: str
    HOST: str
    PORT: int
    
    # CORS (optional, for frontend integration)
    ALLOWED_ORIGINS: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

