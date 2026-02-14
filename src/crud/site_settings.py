from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.site_settings import SiteSetting
from typing import Optional

async def get_setting(db: AsyncSession, key: str) -> Optional[SiteSetting]:
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    return result.scalars().first()

async def set_setting(db: AsyncSession, key: str, value: str) -> SiteSetting:
    setting = await get_setting(db, key)
    if setting:
        setting.value = value
    else:
        setting = SiteSetting(key=key, value=value)
        db.add(setting)
    await db.flush()
    return setting

