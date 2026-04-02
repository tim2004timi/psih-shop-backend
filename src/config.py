from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Public URLs
    HOST: str = "localhost"
    BACKEND_PUBLIC_BASE_URL: str = "http://localhost:8000"
    FRONTEND_PUBLIC_BASE_URL: str = "https://psihclothes.com"
    TRUST_X_FORWARDED_FOR: bool = False

    # Database settings
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "psih-postgres"
    POSTGRES_PORT: str = "5432"
    
    # Database URL
    DATABASE_URL: Optional[str] = None
    TEST_DATABASE_URL: Optional[str] = None
    
    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # MinIO settings
    MINIO_ENDPOINT: str = "psih-minio:9000"
    MINIO_PORT: str = "9000"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "photos"
    MINIO_PUBLIC_BASE_URL: Optional[str] = None
    
    # Application settings
    DEBUG: bool = False
    ENABLE_STARTUP_SCHEMA_SYNC: bool = False
    
    # CORS settings
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://109.172.36.219:3000",
        "https://psihclothes.com",
        "http://psihclothes.com",
    ])
    
    # CDEK API settings
    CDEK_ACCOUNT: Optional[str] = None
    CDEK_SECURE_PASSWORD: Optional[str] = None
    CDEK_API_URL: str = "https://api.cdek.ru/v2"
    CDEK_TEST_MODE: bool = False
    CDEK_PVZ_CODE_FROM: str = "MSK549"
    CDEK_TEST_PVZ_CODE_FROM: str = "MSK5"
    CDEK_TEST_PVZ_CODE_TO: str = "MSK71"
    
    # TBank Payment settings
    TBANK_TERMINAL_KEY: Optional[str] = None
    TBANK_SECRET_KEY: Optional[str] = None
    TBANK_API_URL: str = "https://securepay.tinkoff.ru/v2"
    # These can be overridden in .env for production domain
    TBANK_SUCCESS_URL: str = "https://psihclothes.com/order-success"
    TBANK_FAIL_URL: str = "https://psihclothes.com/order-failed"

    # PayPal Payment settings
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_MODE: str = "sandbox"

    @property
    def paypal_api_url(self) -> str:
        if self.PAYPAL_MODE == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    # Media upload safety
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024
    MAX_IMAGE_PIXELS: int = 20_000_000
    ALLOWED_IMAGE_CONTENT_TYPES: list[str] = Field(default_factory=lambda: [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    ])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if not self.DATABASE_URL:
            self.DATABASE_URL = self.get_database_url()
    
    def get_database_url(self) -> str:
        """Генерирует URL для подключения к PostgreSQL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_async_database_url(self) -> str:
        """Генерирует async URL для подключения к PostgreSQL"""
        import os
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        
        if os.environ.get('FORCE_POSTGRES'):
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

        from pathlib import Path
        db_path = Path(__file__).resolve().parent.parent / "psih_shop_dev.db"
        return f"sqlite+aiosqlite:///{db_path}"

    def get_sync_database_url(self) -> str:
        """Генерирует sync URL для миграций и утилит."""
        if self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
        return self.get_database_url()

    @property
    def api_base_url(self) -> str:
        return self.BACKEND_PUBLIC_BASE_URL.rstrip("/")

    @property
    def minio_public_base_url(self) -> str:
        if self.MINIO_PUBLIC_BASE_URL:
            return self.MINIO_PUBLIC_BASE_URL.rstrip("/")
        scheme = "https" if self.MINIO_SECURE else "http"
        return f"{scheme}://{self.HOST}:{self.MINIO_PORT}"

settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    return Settings()
