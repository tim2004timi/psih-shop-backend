from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.config import settings
from src import crud
from src.schemas.user import UserLogin, UserResponse, UserCreate
from src.utils import verify_password

router = APIRouter()

# OAuth2 схема для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[dict]:
    """Аутентифицирует пользователя по email и паролю"""
    user = await crud.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Получает текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "avatar": user.avatar,
        "address": user.address,
        "city": user.city,
        "postal_code": user.postal_code,
        "country": user.country,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.post("/token",
    summary="Получить токен доступа",
    description="Аутентификация пользователя и получение JWT токена для доступа к защищенным эндпоинтам",
    response_description="Токен доступа и информация о пользователе")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Эндпоинт для получения JWT токена"""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }

@router.post("/register",
    summary="Регистрация нового пользователя",
    description="Создание нового аккаунта пользователя в системе",
    response_description="Токен доступа и информация о созданном пользователе")
async def register_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Эндпоинт для регистрации нового пользователя"""
    # Проверяем, существует ли пользователь с таким email
    existing_user = await crud.get_user_by_email(db, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    

    user = await crud.create_user(db, user_create)
    
    # Создаем токен для нового пользователя
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }

@router.get("/me", 
    response_model=UserResponse,
    summary="Получить информацию о текущем пользователе",
    description="Возвращает информацию о текущем аутентифицированном пользователе")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Эндпоинт для получения информации о текущем пользователе"""
    return current_user

# Дополнительные утилиты (можно вынести в отдельный файл если нужно)
def validate_token(token: str) -> bool:
    """Проверяет валидность JWT токена"""
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return True
    except JWTError:
        return False

def get_email_from_token(token: str) -> Optional[str]:
    """Извлекает email из JWT токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None