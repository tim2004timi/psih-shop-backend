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
                # Разрешаем NULL для weight и проставляем дефолты
                await conn.execute(text("ALTER TABLE products ALTER COLUMN weight DROP NOT_NULL;"))
                await conn.execute(text("UPDATE products SET weight = 0.1 WHERE weight IS NULL OR weight <= 0;"))
                logger.info("Weight column updated to be nullable and default values set")
            except Exception as e:
                logger.warning(f"Weight column update issue: {e}")

            try:
                # 1. Сначала пробуем найти и удалить CONSTRAINT (как раньше)
                constraint_query = text("""
                    SELECT conname
                    FROM pg_constraint
                    WHERE conrelid = 'product_colors'::regclass
                    AND contype = 'u'
                    AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'product_colors'::regclass AND attname = 'slug')];
                """)
                result = await conn.execute(constraint_query)
                constraint_name = result.scalar_one_or_none()

                if constraint_name:
                    await conn.execute(text(f"ALTER TABLE product_colors DROP CONSTRAINT {constraint_name};"))
                    logger.info(f"Dropped unique constraint: {constraint_name}")
                
                # 2. Теперь ищем ЛЮБОЙ уникальный индекс на поле slug, который мог остаться (даже если это не constraint)
                index_query = text("""
                    SELECT i.relname as index_name
                    FROM pg_class t, pg_class i, pg_index ix, pg_attribute a
                    WHERE t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relname = 'product_colors'
                    AND a.attname = 'slug'
                    AND ix.indisunique = true;
                """)
                result = await conn.execute(index_query)
                unique_indexes = result.scalars().all()
                
                for index_name in unique_indexes:
                    await conn.execute(text(f"DROP INDEX IF EXISTS {index_name};"))
                    logger.info(f"Dropped unique index: {index_name}")

                # 3. Чистим стандартные имена на всякий случай
                await conn.execute(text("DROP INDEX IF EXISTS ix_product_colors_slug;"))
                await conn.execute(text("DROP INDEX IF EXISTS product_colors_slug_key;"))
                
                # 4. Создаем обычный (неуникальный) индекс
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_product_colors_slug ON product_colors (slug);"))
                logger.info("Unique constraint removed and normal index created for product_colors.slug")
            except Exception as e:
                logger.warning(f"Error removing unique constraint from product_colors.slug: {e}")
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