from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.models.orders import CustomStatus


async def get_custom_status_by_id(db: AsyncSession, status_id: int) -> Optional[CustomStatus]:
    result = await db.execute(select(CustomStatus).where(CustomStatus.id == status_id))
    return result.scalar_one_or_none()


async def get_custom_status_by_name(db: AsyncSession, name: str) -> Optional[CustomStatus]:
    result = await db.execute(select(CustomStatus).where(CustomStatus.name == name))
    return result.scalar_one_or_none()


async def list_custom_statuses(db: AsyncSession) -> List[CustomStatus]:
    result = await db.execute(select(CustomStatus).order_by(CustomStatus.name))
    return result.scalars().all()


async def create_custom_status(db: AsyncSession, *, name: str) -> CustomStatus:
    status = CustomStatus(name=name)
    db.add(status)
    await db.commit()
    await db.refresh(status)
    return status


async def delete_custom_status(db: AsyncSession, status_id: int) -> bool:
    status = await get_custom_status_by_id(db, status_id)
    if not status:
        return False
    await db.delete(status)
    await db.commit()
    return True
