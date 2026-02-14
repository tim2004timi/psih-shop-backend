"""
TBank Payment Integration Router
Handles payment initialization and webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import hashlib
import logging

from src.database import get_db
from src.auth import get_current_user
from src.models.orders import Order, OrderProduct, OrderStatus
from src.models.product import Product, ProductColor, ProductSize
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

# Pydantic models
class PaymentInitRequest(BaseModel):
    order_id: int
    payment_method: Optional[str] = 'card'
    connection_type: Optional[str] = None
    success_url: Optional[str] = None
    fail_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class PaymentInitResponse(BaseModel):
    success: bool
    payment_url: Optional[str] = None
    payment_id: Optional[str] = None
    error: Optional[str] = None

class TBankNotification(BaseModel):
    TerminalKey: str
    Amount: int
    OrderId: str
    Success: bool
    Status: str
    PaymentId: int
    ErrorCode: str
    Message: Optional[str] = None
    Token: str
    RebillId: Optional[int] = None
    CardId: Optional[int] = None
    Pan: Optional[str] = None
    ExpDate: Optional[str] = None

# TBank API Client
class TBankClient:
    def __init__(self):
        self.terminal_key = settings.TBANK_TERMINAL_KEY
        self.secret_key = settings.TBANK_SECRET_KEY
        self.api_url = settings.TBANK_API_URL
        
    def _generate_token(self, params: dict) -> str:
        """Generate token for TBank API request"""
        token_params = {**params, 'Password': self.secret_key}
        
        excluded = ['Token', 'Receipt', 'DATA', 'Shops', 'Receipts']
        filtered = {k: v for k, v in token_params.items() 
                   if k not in excluded and v is not None and not isinstance(v, (dict, list))}
        
        sorted_keys = sorted(filtered.keys())
        concatenated = ''.join(str(filtered[k]) for k in sorted_keys)
        
        return hashlib.sha256(concatenated.encode()).hexdigest()
    
    def verify_notification_token(self, notification: dict) -> bool:
        """Verify webhook notification token"""
        received_token = notification.get('Token')
        if not received_token:
            return False
        
        params = {k: v for k, v in notification.items() if k != 'Token'}
        expected_token = self._generate_token(params)
        
        return received_token.lower() == expected_token.lower()
    
    async def init_payment(
        self,
        order_id: int,
        amount: int,
        description: str,
        email: Optional[str] = None,
        success_url: Optional[str] = None,
        fail_url: Optional[str] = None,
        connection_type: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        receipt_items: Optional[list] = None
    ) -> dict:
        """Initialize payment and get payment URL"""
        if not self.terminal_key or not self.secret_key:
            raise ValueError("TBank credentials not configured")
        
        params: Dict[str, Any] = {
            'TerminalKey': self.terminal_key,
            'Amount': amount,
            'OrderId': str(order_id),
            'Description': description[:250],
            'SuccessURL': success_url or f"{settings.TBANK_SUCCESS_URL}?orderId={order_id}",
            'FailURL': fail_url or f"{settings.TBANK_FAIL_URL}?orderId={order_id}",
        }
        
        data_obj: Dict[str, Any] = {}
        if email:
            data_obj['Email'] = email
        if connection_type:
            data_obj['connection_type'] = connection_type
        if extra_data:
            data_obj.update(extra_data)
        if data_obj:
            params['DATA'] = data_obj
        
        if receipt_items and email:
            params['Receipt'] = {
                'Email': email,
                'Taxation': 'usn_income',
                'Items': receipt_items
            }
        
        token = self._generate_token(params)
        params['Token'] = token
        
        logger.info(f"Initializing TBank payment for order {order_id}, amount: {amount}, connection_type: {connection_type}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/Init",
                json=params,
                timeout=30.0
            )
            result = response.json()
            
        logger.info(f"TBank Init response: {result}")
        return result


# Global client instance
tbank_client = TBankClient()


@router.post("/init", response_model=PaymentInitResponse)
async def init_payment(
    request: PaymentInitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize payment for an order.
    Returns payment URL for redirect.
    """
    if not settings.TBANK_TERMINAL_KEY or not settings.TBANK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment system not configured"
        )
    
    result = await db.execute(select(Order).where(Order.id == request.order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not current_user.get("is_admin", False):
        if order.user_id != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only pay for your own orders"
            )
    
    if order.status != OrderStatus.NOT_PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order already has status: {order.status.value}"
        )
    
    try:
        amount = int(float(order.total_price) * 100)
        description = f"Заказ #{order.id}"
        
        connection_type = None
        if request.connection_type == 'Widget':
            connection_type = 'Widget'
        elif request.data and request.data.get('connection_type') == 'Widget':
            connection_type = 'Widget'
        
        receipt_items = []
        order_products_result = await db.execute(
            select(OrderProduct).where(OrderProduct.order_id == order.id)
        )
        order_products = order_products_result.scalars().all()
        
        if order_products:
            size_ids = [op.product_size_id for op in order_products]
            sizes_result = await db.execute(select(ProductSize).where(ProductSize.id.in_(size_ids)))
            sizes = {ps.id: ps for ps in sizes_result.scalars().all()}
            
            color_ids = [sizes[op.product_size_id].product_color_id for op in order_products if op.product_size_id in sizes]
            colors_result = await db.execute(select(ProductColor).where(ProductColor.id.in_(color_ids)))
            colors = {pc.id: pc for pc in colors_result.scalars().all()}
            
            product_ids = [colors[cid].product_id for cid in color_ids if cid in colors]
            products_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
            products = {p.id: p for p in products_result.scalars().all()}
            
            for op in order_products:
                ps = sizes.get(op.product_size_id)
                if not ps:
                    continue
                pc = colors.get(ps.product_color_id)
                if not pc:
                    continue
                prod = products.get(pc.product_id)
                if not prod:
                    continue
                
                price = prod.discount_price if prod.discount_price is not None else prod.price
                price_kopecks = int(float(price) * 100)
                item_amount = price_kopecks * op.quantity
                
                receipt_items.append({
                    'Name': f"{pc.title} ({ps.size})"[:64],
                    'Price': price_kopecks,
                    'Quantity': op.quantity,
                    'Amount': item_amount,
                    'Tax': 'none',
                    'PaymentMethod': 'full_payment',
                    'PaymentObject': 'commodity'
                })
        
        if not receipt_items:
            receipt_items.append({
                'Name': description[:64],
                'Price': amount,
                'Quantity': 1,
                'Amount': amount,
                'Tax': 'none',
                'PaymentMethod': 'full_payment',
                'PaymentObject': 'commodity'
            })
        
        response = await tbank_client.init_payment(
            order_id=order.id,
            amount=amount,
            description=description,
            email=order.email,
            success_url=request.success_url,
            fail_url=request.fail_url,
            connection_type=connection_type,
            extra_data=request.data,
            receipt_items=receipt_items
        )
        
        if response.get('Success') and response.get('PaymentURL'):
            order.payment_id = str(response.get('PaymentId'))
            await db.commit()
            
            return PaymentInitResponse(
                success=True,
                payment_url=response.get('PaymentURL'),
                payment_id=str(response.get('PaymentId'))
            )
        else:
            error_msg = response.get('Message') or response.get('Details') or 'Unknown error'
            logger.error(f"TBank Init failed: {response}")
            return PaymentInitResponse(
                success=False,
                error=error_msg
            )
            
    except Exception as e:
        logger.error(f"Payment init error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle TBank payment notifications (webhooks).
    TBank calls this endpoint when payment status changes.
    """
    try:
        body = await request.json()
        logger.info(f"Received TBank webhook: {body}")
        
        # Verify token
        if not tbank_client.verify_notification_token(body):
            logger.warning("Invalid webhook token")
            return {"error": "Invalid token"}
        
        # Get order by OrderId
        order_id = int(body.get('OrderId', 0))
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return "OK"  # Return OK to avoid retries
        
        # Update payment_id if not set
        payment_id = str(body.get('PaymentId'))
        if not order.payment_id:
            order.payment_id = payment_id
        
        # Map TBank status to our status
        tbank_status = body.get('Status')
        success = body.get('Success', False)
        
        logger.info(f"Order {order_id}: TBank status={tbank_status}, success={success}")
        
        if tbank_status in ['CONFIRMED', 'AUTHORIZED']:
            # Payment successful
            order.status = OrderStatus.PAID
            logger.info(f"Order {order_id} marked as PAID")
            
        elif tbank_status in ['REJECTED', 'CANCELLED', 'AUTH_FAIL', 'DEADLINE_EXPIRED']:
            # Payment failed
            order.status = OrderStatus.PAYMENT_FAILED
            logger.info(f"Order {order_id} payment failed: {tbank_status}")
            
        elif tbank_status in ['REFUNDED', 'PARTIAL_REFUNDED']:
            # Refund
            order.status = OrderStatus.CANCELLED
            logger.info(f"Order {order_id} refunded")
        
        await db.commit()
        
        # TBank expects "OK" response
        return "OK"
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return "OK"  # Return OK to avoid retries


@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment status for an order"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check user owns the order or is admin
    if not current_user.get("is_admin", False):
        if order.user_id != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only check your own orders"
            )
    
    return {
        "order_id": order.id,
        "status": order.status.value,
        "payment_id": order.payment_id,
        "is_paid": order.status != OrderStatus.NOT_PAID
    }

