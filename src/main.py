from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import asyncio

from src.database import create_tables, check_db_connection
from src.auth import router as auth_router
from src.routers.user import router as user_router
from src.routers.product import router as product_router
from src.routers.category import router as category_router
from src.routers.collection import router as collection_router


app = FastAPI(
    title="Psih Shop API",
    description="API для интернет-магазина Psih Shop",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await asyncio.sleep(2)

    # Создаем таблицы при старте приложения
    await create_tables()
    # Проверяем подключение к БД
    if await check_db_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")

# Подключаем роутеры
main_router = APIRouter(prefix="/api")
main_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
main_router.include_router(user_router, tags=["Users"])
main_router.include_router(product_router, tags=["Products"])
main_router.include_router(category_router, tags=["Categories"])
main_router.include_router(collection_router, tags=["Collections"])

app.include_router(main_router)


