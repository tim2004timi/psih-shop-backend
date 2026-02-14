import os
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Host
    HOST: str = "localhost"

    # Database settings
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "psih-postgres"
    POSTGRES_PORT: str = "5432"
    
    # Database URL
    DATABASE_URL: Optional[str] = None
    
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
    
    # Application settings
    DEBUG: bool = False
    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://109.172.36.219:3000",
        "https://psihclothes.com",
        "http://psihclothes.com",
    ]
    
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
    TBANK_SUCCESS_URL: str = "https://psihclothes.com/ru/order-success"
    TBANK_FAIL_URL: str = "https://psihclothes.com/ru/order-failed"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'allow' 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if not self.DATABASE_URL:
            self.DATABASE_URL = self.get_database_url()
    
    def get_database_url(self) -> str:
        """Генерирует URL для подключения к PostgreSQL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_async_database_url(self) -> str:
        """Генерирует async URL для подключения к PostgreSQL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    return Settings()
