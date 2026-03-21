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
import re
from fastapi import HTTPException, status

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


DERIVATIVE_SUFFIXES = ("medium", "small", "thumb")

CACHE_HEADERS = {"Cache-Control": "public, max-age=31536000, immutable"}


def generate_object_name(filename: str) -> dict[str, str]:
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    uid = str(uuid.uuid4())
    return {
        "original": f"{uid}{ext}",
        "medium": f"{uid}-medium.webp",
        "small": f"{uid}-small.webp",
        "thumb": f"{uid}-thumb.webp",
    }


def build_public_url(object_name: str) -> str:
    return f"{settings.minio_public_base_url}/{settings.MINIO_BUCKET_NAME}/{object_name}"


def _open_and_prepare(content: bytes) -> Image.Image:
    Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
    img = Image.open(BytesIO(content))
    img.verify()
    img = Image.open(BytesIO(content))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    return img


def resize_image_jpeg(content: bytes, max_width: int, quality: int = 92) -> bytes:
    """Resize keeping the original format (JPEG) at high quality."""
    img = _open_and_prepare(content)
    w, h = img.size
    if w <= max_width and h <= max_width:
        return content
    if w > h:
        ratio = max_width / float(w)
    else:
        ratio = max_width / float(h)
    new_size = (int(w * ratio), int(h * ratio))
    resized = img.resize(new_size, Image.LANCZOS)
    out = BytesIO()
    resized.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def resize_image_webp(content: bytes, max_width: int, quality: int = 90) -> bytes:
    """Resize and convert to WebP via Pillow (much better quality than
    browser Canvas WebP encoding)."""
    img = _open_and_prepare(content)
    w, h = img.size
    if w > h:
        ratio = min(1.0, max_width / float(w))
    else:
        ratio = min(1.0, max_width / float(h))
    new_size = (int(w * ratio), int(h * ratio))
    resized = img.resize(new_size, Image.LANCZOS) if ratio < 1.0 else img
    out = BytesIO()
    resized.save(out, format="WEBP", quality=quality, method=6)
    return out.getvalue()


def _upload_bytes(client, bucket: str, name: str, data: bytes, content_type: str):
    client.put_object(
        bucket,
        name,
        data=BytesIO(data),
        length=len(data),
        content_type=content_type,
        metadata=CACHE_HEADERS,
    )


async def upload_image_and_derivatives(file, filename: str) -> str:
    """Upload file and derivatives, return main file URL."""
    try:
        content_type = getattr(file, "content_type", None)
        if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported image type",
            )

        client = get_minio_client()
        names = generate_object_name(filename)
        bucket = settings.MINIO_BUCKET_NAME

        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info(f"Created MinIO bucket: {bucket}")

        file_bytes = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
        await file.seek(0)

        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large",
            )

        original_bytes = resize_image_jpeg(file_bytes, 2400, quality=92)
        _upload_bytes(client, bucket, names["original"], original_bytes, "image/jpeg")

        medium_bytes = resize_image_webp(file_bytes, 1200, quality=90)
        _upload_bytes(client, bucket, names["medium"], medium_bytes, "image/webp")

        small_bytes = resize_image_webp(file_bytes, 600, quality=88)
        _upload_bytes(client, bucket, names["small"], small_bytes, "image/webp")

        thumb_bytes = resize_image_webp(file_bytes, 300, quality=80)
        _upload_bytes(client, bucket, names["thumb"], thumb_bytes, "image/webp")

        logger.info(f"Successfully uploaded image with derivatives: {names['original']}")
        return build_public_url(names["original"])
    except Exception as e:
        logger.error(f"Failed to upload image {filename}: {str(e)}", exc_info=True)
        raise


def copy_image_in_minio(source_url: str) -> str:
    """Copy an image and all its derivatives in MinIO (server-side). Returns new public URL."""
    if not source_url:
        raise ValueError("source_url is empty")

    parts = source_url.split('/')
    source_object = parts[-1]
    name, ext = os.path.splitext(source_object)

    new_uid = str(uuid.uuid4())
    new_original = f"{new_uid}{ext}"

    source_objects = [source_object] + [f"{name}-{s}.webp" for s in DERIVATIVE_SUFFIXES]
    dest_objects = [new_original] + [f"{new_uid}-{s}.webp" for s in DERIVATIVE_SUFFIXES]

    client = get_minio_client()
    bucket = settings.MINIO_BUCKET_NAME
    from minio.commonconfig import CopySource

    for src, dst in zip(source_objects, dest_objects):
        try:
            client.copy_object(bucket, dst, CopySource(bucket, src))
        except Exception as e:
            logger.warning(f"Failed to copy {src} -> {dst}: {e}")

    return build_public_url(new_original)


async def delete_image_from_minio(file_url: str):
    """Delete image and its derivatives from MinIO."""
    try:
        if not file_url:
            return

        parts = file_url.split('/')
        if len(parts) < 2:
            return

        base_object_name = parts[-1]
        bucket = settings.MINIO_BUCKET_NAME
        client = get_minio_client()

        name, _ext = os.path.splitext(base_object_name)

        objects_to_delete = [
            base_object_name,
            f"{name}-medium.webp",
            f"{name}-small.webp",
            f"{name}-thumb.webp",
        ]

        for obj in objects_to_delete:
            try:
                client.remove_object(bucket, obj)
                logger.info(f"Deleted object from MinIO: {obj}")
            except Exception as e:
                logger.warning(f"Failed to delete object {obj} from MinIO: {e}")

    except Exception as e:
        logger.error(f"Error in delete_image_from_minio: {e}", exc_info=True)