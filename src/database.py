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
                await conn.execute(text("ALTER TABLE products ALTER COLUMN weight DROP NOT NULL;"))
                await conn.execute(text("UPDATE products SET weight = 0.1 WHERE weight IS NULL OR weight <= 0;"))
                logger.info("Weight column updated to be nullable and default values set")
            except Exception as e:
                logger.warning(f"Weight column update issue: {e}")

            try:
                await conn.execute(text("""
                    DO $$
                    DECLARE r record;
                    BEGIN
                        FOR r IN
                            SELECT c.conname AS name
                            FROM pg_constraint c
                            JOIN pg_class t ON t.oid = c.conrelid
                            WHERE t.relname = 'product_colors'
                              AND c.contype = 'u'
                              AND array_length(c.conkey, 1) = 1
                              AND (
                                SELECT a.attname
                                FROM pg_attribute a
                                WHERE a.attrelid = t.oid AND a.attnum = c.conkey[1]
                              ) = 'slug'
                        LOOP
                            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I', 'product_colors', r.name);
                        END LOOP;

                        FOR r IN
                            SELECT i.relname AS name
                            FROM pg_class t
                            JOIN pg_index ix ON t.oid = ix.indrelid
                            JOIN pg_class i ON i.oid = ix.indexrelid
                            WHERE t.relname = 'product_colors'
                              AND ix.indisunique = true
                              AND array_length(ix.indkey::smallint[], 1) = 1
                              AND (
                                SELECT a.attname
                                FROM pg_attribute a
                                WHERE a.attrelid = t.oid AND a.attnum = (ix.indkey::smallint[])[1]
                              ) = 'slug'
                        LOOP
                            EXECUTE format('DROP INDEX IF EXISTS %I', r.name);
                        END LOOP;
                    END $$;
                """))

                await conn.execute(text("DROP INDEX IF EXISTS ix_product_colors_slug;"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_product_colors_slug ON product_colors (slug);"))
                logger.info("product_colors.slug index verified")
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
