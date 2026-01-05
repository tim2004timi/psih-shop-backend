from passlib.context import CryptContext
from minio import Minio
from io import BytesIO
from PIL import Image
import uuid
import os
from src.config import settings
import mimetypes
import bcrypt
import logging

import logging
import re

logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """Генерирует slug из текста, поддерживает кириллицу"""
    cyrillic_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
        'я': 'ya'
    }
    
    text = text.lower()
    for char, replacement in cyrillic_map.items():
        text = text.replace(char, replacement)
    
    # Оставляем только буквы, цифры и дефисы
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Удаляем лишние дефисы
    text = re.sub(r'-+', '-', text).strip('-')
    return text

# Настройка для хеширования паролей
# Используем bcrypt напрямую для избежания проблем с автоматическим определением backend в passlib
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля и хеша"""
    if not hashed_password or not plain_password:
        return False
    
    # Проверяем, что хеш имеет правильный формат bcrypt
    if not hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
        return False
    
    # Bcrypt имеет ограничение в 72 байта для пароля
    # Обрезаем пароль, если он длиннее
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    try:
        # Используем bcrypt напрямую для избежания проблем с passlib
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except (ValueError, TypeError, Exception):
        # Если хеш некорректен или произошла другая ошибка, пробуем через passlib
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except (ValueError, TypeError, Exception):
            return False

def get_password_hash(password: str) -> str:
    """Генерирует хеш пароля"""
    # Bcrypt имеет ограничение в 72 байта для пароля
    # Обрезаем пароль, если он длиннее
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Используем bcrypt напрямую для избежания проблем с passlib
    # Генерируем соль и хешируем пароль
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def get_minio_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE,
    )


def generate_object_name(filename: str) -> tuple[str, str, str]:
    ext = os.path.splitext(filename)[1].lower()
    uid = str(uuid.uuid4())
    base = f"{uid}{ext}"
    medium = f"{uid}-medium{ext}"
    small = f"{uid}-small{ext}"
    return base, medium, small


def build_public_url(object_name: str) -> str:
    return f"http://{settings.HOST}:{settings.MINIO_PORT}/{settings.MINIO_BUCKET_NAME}/{object_name}"


def resize_image(content: bytes, max_width: int) -> bytes:
    image = Image.open(BytesIO(content))
    if image.mode in ("RGBA", "P"):  # конвертим только если нужно
        image = image.convert("RGB")
    w, h = image.size
    if w <= max_width:
        return content
    ratio = max_width / float(w)
    new_size = (max_width, int(h * ratio))
    resized = image.resize(new_size, Image.LANCZOS)
    out = BytesIO()
    fmt = image.format or "JPEG"
    resized.save(out, format=fmt, quality=85, optimize=True)
    return out.getvalue()


async def upload_image_and_derivatives(file, filename: str) -> str:
    """Upload file and derivatives, return main file URL"""
    try:
        client = get_minio_client()
        base, medium, small = generate_object_name(filename)
        bucket = settings.MINIO_BUCKET_NAME

        # ensure bucket exists
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info(f"Created MinIO bucket: {bucket}")

        # read file content
        file_bytes = await file.read()
        await file.seek(0)  # reset file pointer

        # detect content-types
        base_ct, _ = mimetypes.guess_type(base)
        medium_ct, _ = mimetypes.guess_type(medium)
        small_ct, _ = mimetypes.guess_type(small)
        base_ct = base_ct or "image/jpeg"
        medium_ct = medium_ct or base_ct
        small_ct = small_ct or base_ct

        # upload original
        client.put_object(bucket, base, data=BytesIO(file_bytes), length=len(file_bytes), content_type=base_ct)

        # medium and small
        medium_bytes = resize_image(file_bytes, 1200)
        small_bytes = resize_image(file_bytes, 800)
        client.put_object(bucket, medium, data=BytesIO(medium_bytes), length=len(medium_bytes), content_type=medium_ct)
        client.put_object(bucket, small, data=BytesIO(small_bytes), length=len(small_bytes), content_type=small_ct)

        logger.info(f"Successfully uploaded image: {base}")
        return build_public_url(base)
    except Exception as e:
        logger.error(f"Failed to upload image {filename}: {str(e)}", exc_info=True)
        raise

async def delete_image_from_minio(file_url: str):
    """Delete image and its derivatives from MinIO"""
    try:
        if not file_url:
            return
        
        # URL format: http://host:port/bucket/object_name
        # We need to extract object_name
        parts = file_url.split('/')
        if len(parts) < 2:
            return
        
        base_object_name = parts[-1]
        bucket = settings.MINIO_BUCKET_NAME
        client = get_minio_client()
        
        # Get filename and extension
        name, ext = os.path.splitext(base_object_name)
        
        # List of objects to delete
        objects_to_delete = [
            base_object_name,
            f"{name}-medium{ext}",
            f"{name}-small{ext}"
        ]
        
        for obj in objects_to_delete:
            try:
                client.remove_object(bucket, obj)
                logger.info(f"Deleted object from MinIO: {obj}")
            except Exception as e:
                logger.warning(f"Failed to delete object {obj} from MinIO: {e}")
                
    except Exception as e:
        logger.error(f"Error in delete_image_from_minio: {e}", exc_info=True)