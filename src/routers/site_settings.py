from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.auth import get_current_user
from src.crud.site_settings import get_setting, set_setting
from src.schemas.site_settings import SiteSettingPublic, SiteSettingUpdate
from src.utils import upload_image_and_derivatives
import json

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/{key}", response_model=SiteSettingPublic)
async def get_site_setting(key: str, db: AsyncSession = Depends(get_db)):
    setting = await get_setting(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{key}", response_model=SiteSettingPublic)
async def update_site_setting(
    key: str, 
    setting_update: SiteSettingUpdate, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    setting = await set_setting(db, key, setting_update.value)
    return setting

@router.post("/upload-banner", summary="Загрузить баннер для главной страницы")
async def upload_banner(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    file_url = await upload_image_and_derivatives(file, file.filename)
    return {"url": file_url}

