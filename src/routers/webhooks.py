from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import ipaddress

from src.database import get_db
from src.models.orders import Order

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])

_CDEK_ALLOWED_CIDRS = (
    ipaddress.ip_network("194.49.120.0/24"),
    ipaddress.ip_network("195.189.222.0/24"),
    ipaddress.ip_network("194.49.121.0/24"),
)


def _get_client_ip(request: Request) -> str | None:
    # If behind proxy, the first IP in X-Forwarded-For is the client.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _is_allowed_cdek_ip(ip_str: str | None) -> bool:
    if not ip_str:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(ip_obj in net for net in _CDEK_ALLOWED_CIDRS)


@router.post("/webhook/order_status")
async def cdek_order_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    CDEK webhook: ORDER_STATUS.
    Обновляет поле cdek_status по номеру заказа в нашей системе.
    """
    client_ip = _get_client_ip(request)
    if not _is_allowed_cdek_ip(client_ip):
        logger.warning(f"CDEK webhook: forbidden IP {client_ip}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    
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
