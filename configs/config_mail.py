"""
Email configuration module for SMTP settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MailSettings(BaseSettings):
    """Email settings from environment variables"""
    
    # SMTP Configuration
    MAIL_HOST: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM_ADDRESS: str = ""
    MAIL_FROM_NAME: str = "Auction System"
    
    # Email settings
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_TIMEOUT: int = 30
    
    # App settings
    APP_URL: str = "http://localhost:8000"
    SUPPORT_EMAIL: str = "support@auction.com"
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:5173"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global mail settings instance
mail_settings = MailSettings()