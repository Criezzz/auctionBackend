"""
Email configuration module for SMTP settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MailSettings(BaseSettings):
    """Email settings from environment variables"""
    
    # SMTP Configuration
    MAIL_HOST: str
    MAIL_PORT: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM_ADDRESS: str
    MAIL_FROM_NAME: str
    
    # Email settings
    MAIL_USE_TLS: bool
    MAIL_USE_SSL: bool
    MAIL_TIMEOUT: int
    
    # App settings
    APP_URL: str
    SUPPORT_EMAIL: str
    
    # Frontend URL for email links
    FRONTEND_URL: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global mail settings instance
mail_settings = MailSettings()