from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from src.database import create_tables, check_db_connection
from src.config import settings
from src.auth import router as auth_router
from src.routers.user import router as user_router
from src.routers.product import router as product_router
from src.routers.category import router as category_router
from src.routers.collection import router as collection_router
from src.routers.orders import router as orders_router
from src.routers.custom_statuses import router as custom_statuses_router
from src.routers.cdek import router as cdek_router
from src.routers.payments import router as payments_router
from src.routers.site_settings import router as settings_router
from src.routers.webhooks import router as webhooks_router
from src.routers.promocode import router as promocode_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.sleep(2)

    logger.info("Starting application...")

    if settings.ENABLE_STARTUP_SCHEMA_SYNC:
        logger.warning("ENABLE_STARTUP_SCHEMA_SYNC is enabled. Prefer Alembic migrations in production.")
        try:
            await create_tables()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
            raise

    if await check_db_connection():
        logger.info("Database connection is healthy")
    else:
        logger.error("Database connection failed")

    yield


app = FastAPI(
    title="Psih Shop API",
    description="API для интернет-магазина Psih Shop",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для предотвращения кэширования API ответов
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Подключаем роутеры
main_router = APIRouter(prefix="/api")
main_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
main_router.include_router(user_router, tags=["Users"])
main_router.include_router(product_router, tags=["Products"])
main_router.include_router(category_router, tags=["Categories"])
main_router.include_router(collection_router, tags=["Collections"])
main_router.include_router(orders_router, tags=["Orders"])
main_router.include_router(custom_statuses_router, tags=["CustomStatus"])
main_router.include_router(cdek_router, tags=["CDEK"])
main_router.include_router(payments_router, tags=["Payments"])
main_router.include_router(settings_router, tags=["Settings"])
main_router.include_router(webhooks_router, tags=["Webhooks"])
main_router.include_router(promocode_router, tags=["PromoCodes"])

app.include_router(main_router)


