from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "ShopBack"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "production"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super_secret_jwt_key_affiliate_cashback_12345_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    INVOLVE_API_KEY: str = os.getenv("INVOLVE_API_KEY", "")
    INVOLVE_API_SECRET: str = os.getenv("INVOLVE_API_SECRET", "")
    INVOLVE_PROPERTY_ID: int = int(os.getenv("INVOLVE_PROPERTY_ID", "1093569"))
    INVOLVE_AFF_ID: str = os.getenv("INVOLVE_AFF_ID", "1173402")
    INVOLVE_BASE_URL: str = os.getenv("INVOLVE_BASE_URL", "https://api.involve.asia")

    
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "webhook_secret_cashback_2026")
    WEBHOOK_HMAC_SECRET: str = os.getenv("WEBHOOK_HMAC_SECRET", "hmac_secret_shopback_callbacks_2026")
    
    # Advanced Security Features
    ENABLE_HSTS: bool = os.getenv("ENABLE_HSTS", "false").lower() in ("true", "1", "yes")
    TOKEN_REVOCATION_ENABLED: bool = True
    MAX_CALLBACK_AGE_SECONDS: int = 300 # 5 minutes replay window

    # Rate limiting / Fraud Detection
    MAX_LINKS_PER_MINUTE: int = 10
    MAX_LINKS_PER_DAY: int = 100

    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
