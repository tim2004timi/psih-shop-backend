from sqlalchemy import select, or_, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.orders import Order, OrderProduct, DeliveryMethod, CustomStatus
from src.models.product import Product, ProductColor, ProductSize
from src.models.promocode import PromoCode, DiscountType
from src.schemas.orders import OrderCreate, OrderProductCreate, OrderDetail, OrderProductDetail, OrderUpdate
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
import logging
import secrets

logger = logging.getLogger(__name__)

async def create_order(
    db: AsyncSession,
    order_data: OrderCreate,
    products: List[OrderProductCreate]
) -> Order:
    """
    Создать заказ со всеми валидациями.
    
    Валидации:
    - Проверка наличия всех ProductSize
    - Проверка достаточности количества товаров
    - Вычисление total_price
    - Обновление quantity в ProductSize
    """
    if not products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one product"
        )
    
    # Получаем все ID размеров продуктов
    product_size_ids = list(dict.fromkeys(p.product_size_id for p in products))
    
    # Загружаем все ProductSize
    result = await db.execute(
        select(ProductSize)
        .where(ProductSize.id.in_(product_size_ids))
        .with_for_update()
    )
    product_sizes = result.scalars().all()
    
    # Проверяем, что все размеры найдены
    found_ids = {ps.id for ps in product_sizes}
    missing_ids = set(product_size_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product sizes not found: {missing_ids}"
        )
    
    # Создаем словарь для быстрого доступа
    product_size_map = {ps.id: ps for ps in product_sizes}
    
    # Загружаем ProductColor для получения product_id
    product_color_ids = [ps.product_color_id for ps in product_sizes]
    product_colors_result = await db.execute(
        select(ProductColor)
        .where(ProductColor.id.in_(product_color_ids))
    )
    product_colors = product_colors_result.scalars().all()
    product_color_map = {pc.id: pc for pc in product_colors}
    
    # Загружаем Product для получения цен
    product_ids = [pc.product_id for pc in product_colors]
    products_result = await db.execute(
        select(Product)
        .where(Product.id.in_(product_ids))
    )
    products_list = products_result.scalars().all()
    product_map = {p.id: p for p in products_list}
    
    # Валидация количества и вычисление total_price
    total_price = Decimal("0.00")
    updates = []  # Список обновлений для ProductSize
    
    for order_product in products:
        product_size = product_size_map[order_product.product_size_id]
        
        # Проверяем достаточность количества
        if product_size.quantity < order_product.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient quantity for product size {order_product.product_size_id}. "
                       f"Available: {product_size.quantity}, Requested: {order_product.quantity}"
            )
        
        # Получаем цену продукта
        product_color = product_color_map[product_size.product_color_id]
        product = product_map[product_color.product_id]
        
        # Используем discount_price если есть, иначе price
        price = product.discount_price if product.discount_price is not None else product.price
        
        # Добавляем к общей стоимости (конвертируем в Decimal для точных вычислений)
        total_price += Decimal(str(price)) * Decimal(str(order_product.quantity))
        
        # Подготавливаем обновление quantity
        new_quantity = product_size.quantity - order_product.quantity
        product_size.quantity = new_quantity
        updates.append(product_size)
    
    # Добавляем стоимость доставки
    delivery_cost = Decimal("300.00")
    total_price += delivery_cost
    
    # Промокод
    promo_code_id = None
    discount_amount = Decimal("0")
    if order_data.promo_code:
        result = await db.execute(
            select(PromoCode).where(PromoCode.code == order_data.promo_code.upper().strip())
        )
        promo = result.scalar_one_or_none()
        if promo and promo.is_active:
            expired = promo.expires_at and promo.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
            exhausted = promo.max_uses and promo.used_count >= promo.max_uses
            items_total = total_price - delivery_cost
            if not expired and not exhausted:
                if promo.discount_type == DiscountType.PERCENTAGE:
                    discount_amount = (items_total * promo.discount_value / Decimal("100")).quantize(Decimal("0.01"))
                else:
                    discount_amount = min(promo.discount_value, items_total)
                total_price -= discount_amount
                promo_code_id = promo.id
                promo.used_count = (promo.used_count or 0) + 1
    
    # Создаем заказ
    order = Order(
        email=order_data.email,
        first_name=order_data.first_name,
        last_name=order_data.last_name,
        phone=order_data.phone,
        city=order_data.city,
        postal_code=order_data.postal_code,
        address=order_data.address,
        comment=order_data.comment,
        total_price=total_price,
        delivery_method=DeliveryMethod.CDEK,
        status=order_data.status,
        user_id=order_data.user_id,
        promo_code_id=promo_code_id,
        discount_amount=discount_amount,
        access_token=secrets.token_hex(32),
    )
    
    db.add(order)
    await db.flush()  # Получаем ID заказа
    
    # Создаем записи OrderProduct
    order_products = []
    for order_product in products:
        order_product_db = OrderProduct(
            order_id=order.id,
            product_size_id=order_product.product_size_id,
            quantity=order_product.quantity
        )
        db.add(order_product_db)
        order_products.append(order_product_db)
    
    # Обновляем quantity в ProductSize
    for product_size in updates:
        db.add(product_size)
    
    try:
        await db.commit()
        await db.refresh(order)
        logger.info(f"Order {order.id} created successfully with {len(products)} products")
        return order
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

async def get_orders(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[Order]:
    """Get orders list with pagination"""
    query = select(Order)
    if search:
        search_value = search.strip()
        if search_value:
            query = query.outerjoin(CustomStatus, Order.custom_status_id == CustomStatus.id)
            filters = [
                Order.email.ilike(f"%{search_value}%"),
                Order.phone.ilike(f"%{search_value}%"),
                cast(Order.status, String).ilike(f"%{search_value}%"),
                Order.cdek_status.ilike(f"%{search_value}%"),
                Order.cdek_number.ilike(f"%{search_value}%"),
                CustomStatus.name.ilike(f"%{search_value}%"),
            ]
            if search_value.isdigit():
                filters.append(Order.id == int(search_value))
            query = query.where(or_(*filters))

    result = await db.execute(
        query
        .offset(skip)
        .limit(limit)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()
async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    """Получить заказ по ID"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_order_by_access_token(db: AsyncSession, access_token: str) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.access_token == access_token))
    return result.scalar_one_or_none()

async def update_order(
    db: AsyncSession,
    order_id: int,
    order_update: OrderUpdate
) -> Optional[Order]:
    """Обновить заказ (только статус)"""
    order = await get_order_by_id(db, order_id)
    if not order:
        return None

    fields_set = getattr(order_update, "model_fields_set", None)
    if fields_set is None:
        fields_set = order_update.__fields_set__

    # Update only provided fields
    if "status" in fields_set:
        order.status = order_update.status

    if "custom_status_id" in fields_set:
        if order_update.custom_status_id is not None:
            result = await db.execute(
                select(CustomStatus).where(CustomStatus.id == order_update.custom_status_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Custom status not found"
                )
        order.custom_status_id = order_update.custom_status_id

    try:
        await db.commit()
        await db.refresh(order)
        logger.info(f"Order {order_id} updated: status={order.status}")
        return order
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating order {order_id}: {str(e)}", exc_info=True)
        raise

async def get_order_detail(
    db: AsyncSession,
    order_id: int,
    *,
    include_access_token: bool = False,
) -> Optional[OrderDetail]:
    """
    Получить полную информацию о заказе с товарами.
    
    Возвращает:
    - Всю информацию о заказе
    - Список товаров с полной информацией (Product, ProductColor, размер, количество)
    """
    # Получаем заказ
    order = await get_order_by_id(db, order_id)
    if not order:
        return None

    custom_status_name = None
    if order.custom_status_id is not None:
        custom_status_result = await db.execute(
            select(CustomStatus.name).where(CustomStatus.id == order.custom_status_id)
        )
        custom_status_name = custom_status_result.scalar_one_or_none()
    
    # Получаем все товары заказа
    order_products_result = await db.execute(
        select(OrderProduct)
        .where(OrderProduct.order_id == order_id)
    )
    order_products = order_products_result.scalars().all()
    
    if not order_products:
        return OrderDetail(
            id=order.id,
            email=order.email,
            first_name=order.first_name,
            last_name=order.last_name,
            phone=order.phone,
            city=order.city,
            postal_code=order.postal_code,
            address=order.address,
            comment=order.comment,
            total_price=order.total_price,
            delivery_method=order.delivery_method,
            status=order.status,
            custom_status_name=custom_status_name,
            user_id=order.user_id,
            access_token=order.access_token if include_access_token else None,
            cdek_uuid=order.cdek_uuid,
            cdek_number=order.cdek_number,
            promo_code_id=order.promo_code_id,
            discount_amount=order.discount_amount or Decimal("0"),
            created_at=order.created_at,
            products=[]
        )
    
    # Получаем все ProductSize
    product_size_ids = [op.product_size_id for op in order_products]
    product_sizes_result = await db.execute(
        select(ProductSize)
        .where(ProductSize.id.in_(product_size_ids))
    )
    product_sizes = product_sizes_result.scalars().all()
    product_size_map = {ps.id: ps for ps in product_sizes}
    
    # Получаем все ProductColor
    product_color_ids = [ps.product_color_id for ps in product_sizes]
    product_colors_result = await db.execute(
        select(ProductColor)
        .where(ProductColor.id.in_(product_color_ids))
    )
    product_colors = product_colors_result.scalars().all()
    product_color_map = {pc.id: pc for pc in product_colors}
    
    # Получаем все Product
    product_ids = [pc.product_id for pc in product_colors]
    products_result = await db.execute(
        select(Product)
        .where(Product.id.in_(product_ids))
    )
    products = products_result.scalars().all()
    product_map = {p.id: p for p in products}
    
    # Формируем список товаров с полной информацией
    products_detail = []
    for order_product in order_products:
        product_size = product_size_map.get(order_product.product_size_id)
        if not product_size:
            logger.warning(f"Order {order_id}: ProductSize {order_product.product_size_id} not found (deleted?)")
            continue
        product_color = product_color_map.get(product_size.product_color_id)
        if not product_color:
            logger.warning(f"Order {order_id}: ProductColor {product_size.product_color_id} not found (deleted?)")
            continue
        product = product_map.get(product_color.product_id)
        if not product:
            logger.warning(f"Order {order_id}: Product {product_color.product_id} not found (deleted?)")
            continue
        
        products_detail.append(OrderProductDetail(
            id=order_product.id,
            product_id=product.id,
            product_color_id=product_color.id,
            slug=product_color.slug,
            title=product_color.title,
            label=product_color.label,
            hex=product_color.hex,
            price=product.price,
            discount_price=product.discount_price,
            currency=product.currency,
            size=product_size.size,
            quantity=order_product.quantity
        ))
    
    return OrderDetail(
        id=order.id,
        email=order.email,
        first_name=order.first_name,
        last_name=order.last_name,
        phone=order.phone,
        city=order.city,
        postal_code=order.postal_code,
        address=order.address,
        comment=order.comment,
        total_price=order.total_price,
        delivery_method=order.delivery_method,
        status=order.status,
        custom_status_name=custom_status_name,
        user_id=order.user_id,
        access_token=order.access_token if include_access_token else None,
        cdek_uuid=order.cdek_uuid,
        cdek_number=order.cdek_number,
        promo_code_id=order.promo_code_id,
        discount_amount=order.discount_amount or Decimal("0"),
        created_at=order.created_at,
        products=products_detail
    )

async def get_orders_detail(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[OrderDetail]:
    """Получить список всех заказов с полной информацией о товарах"""
    orders = await get_orders(db, skip, limit, search)
    orders_detail = []
    
    for order in orders:
        order_detail = await get_order_detail(db, order.id, include_access_token=False)
        if order_detail:
            orders_detail.append(order_detail)
    
    return orders_detail

