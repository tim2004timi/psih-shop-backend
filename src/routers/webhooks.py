from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from src.database import get_db
from src.models.orders import Order

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


@router.post("/webhook/order_status")
async def cdek_order_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    CDEK webhook: ORDER_STATUS.
    Обновляет поле cdek_status по номеру заказа в нашей системе.
    """
    try:
        body = await request.json()
    except Exception:
        logger.warning("CDEK webhook: invalid JSON body")
        return "OK"
    
    if body.get("type") != "ORDER_STATUS":
        return "OK"
    
    attributes = body.get("attributes") or {}
    status_code = attributes.get("code")
    order_uuid = body.get("uuid")
    
    if not status_code or not order_uuid:
        logger.warning("CDEK webhook: missing status_code or order_uuid")
        return "OK"
    
    order_id = None
    try:
        order_id = int(str(order_uuid))
    except Exception:
        logger.warning(f"CDEK webhook: order_uuid is not int: {order_uuid}")
        return "OK"
    
    try:
        result = await db.execute(select(Order).where(Order.cdek_uuid == order_uuid))
        order = result.scalar_one_or_none()
        if not order:
            logger.warning(f"CDEK webhook: order not found: {order_uuid}")
            return "OK"
        
        order.cdek_status = status_code
        await db.commit()
    except Exception as e:
        logger.error(f"CDEK webhook error: {str(e)}", exc_info=True)
    
    return "OK"
