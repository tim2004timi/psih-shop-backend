import logging

from fastapi import HTTPException, UploadFile, status

from src.config import settings
from src.utils import upload_image_and_derivatives

logger = logging.getLogger(__name__)


async def upload_image(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    try:
        return await upload_image_and_derivatives(file, file.filename)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Image upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image",
        )


def validate_public_image_type(content_type: str | None) -> None:
    if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type",
        )
