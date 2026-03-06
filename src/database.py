import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings

logger = logging.getLogger(__name__)

from src.models.base import Base
# Импортируем все модели для создания таблиц
from src.models.user import User
from src.models.product import Product
from src.models.category import Category, ProductCategory
from src.models.collection import Collection, CollectionImage, CollectionProduct
from src.models.orders import Order, OrderProduct
from src.models.promocode import PromoCode
from src.models.site_settings import SiteSetting

SQLALCHEMY_DATABASE_URL = settings.get_async_database_url()

engine_kwargs = {
    "echo": False,
    "future": True,
}

if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,
    })

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

# Создаем асинхронную сессию
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    """Возвращает сессию БД без неявного коммита."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction error: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()

async def create_tables():
    """Создает таблицы только для локальной и тестовой инициализации."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_tables():
    """
    Удаляет все таблицы из базы данных.
    Используется для тестов.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def check_db_connection():
    """
    Проверяет подключение к базе данных.
    Возвращает True если подключение успешно.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        return False
