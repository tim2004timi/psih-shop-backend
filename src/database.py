from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

from src.models.base import Base
# Импортируем все модели для создания таблиц
from src.models.user import User
from src.models.product import Product
from src.models.category import Category, ProductCategory
from src.models.collection import Collection, CollectionImage, CollectionProduct
from src.models.orders import Order, OrderProduct

# Асинхронный URL для подключения к PostgreSQL
SQLALCHEMY_DATABASE_URL = settings.get_async_database_url()

# Создаем асинхронный engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Логирование SQL запросов (отключите в production)
    pool_size=5,  # Минимальное количество соединений в пуле
    max_overflow=10,  # Максимальное количество дополнительных соединений
    pool_timeout=30,  # Тайм-аут ожидания свободного соединения
    pool_recycle=3600,  # Пересоздавать соединения каждый час
    future=True,  # Для поддержки SQLAlchemy 2.0
)

# Создаем асинхронную сессию
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

# Dependency для получения асинхронной сессии
async def get_db() -> AsyncSession:
    """
    Асинхронная dependency для получения сессии БД.
    Использование:
        async with get_db() as db:
            # работа с БД
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction error: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()

# Функция для создания таблиц
async def create_tables():
    """
    Создает все таблицы в базе данных.
    Вызывается при старте приложения.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with engine.begin() as conn:
            # Пытаемся добавить колонки по одной с индивидуальной обработкой
            try:
                await conn.execute(text("ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;"))
                logger.info("Column sort_order verified in product_categories")
            except Exception as e:
                logger.error(f"Error adding sort_order to product_categories: {e}")
            try:
                await conn.execute(text("ALTER TABLE product_sizes ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;"))
                logger.info("Column sort_order verified in product_sizes")
            except Exception as e:
                logger.error(f"Error adding sort_order to product_sizes: {e}")
            
            try:
                # Изменяем тип колонки weight на DOUBLE PRECISION (Float) с явным преобразованием
                await conn.execute(text("ALTER TABLE products ALTER COLUMN weight TYPE DOUBLE PRECISION USING weight::DOUBLE PRECISION;"))
                logger.info("Column weight type updated to DOUBLE PRECISION in products")
            except Exception as e:
                logger.debug(f"Note: Weight type update might have been skipped or already done: {e}")
    except Exception as e:
        logger.error(f"General migration error: {e}")

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