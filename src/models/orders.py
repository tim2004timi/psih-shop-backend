from sqlalchemy import Column, Integer, String, Numeric, DateTime, func, Enum, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from src.models.base import Base
import enum

class OrderStatus(str, enum.Enum):
    NOT_PAID = "not_paid"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    PAYMENT_FAILED = "payment_failed"

class DeliveryMethod(str, enum.Enum):
    CDEK = "cdek"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(15), nullable=True)
    city = Column(String(50), nullable=True)
    postal_code = Column(String(10), nullable=True)
    address = Column(String(200), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=False)
    delivery_method = Column(Enum(DeliveryMethod), default=DeliveryMethod.CDEK)
    status = Column(Enum(OrderStatus), default=OrderStatus.NOT_PAID)
    cdek_uuid = Column(String(100), nullable=True)
    cdek_status = Column(String(50), nullable=True)
    payment_id = Column(String(50), nullable=True, index=True)  # TBank PaymentId
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint('total_price > 0', name='check_total_price_positive'),
    )

    def __repr__(self):
        return f"<Order(id={self.id}, email={self.email}, status={self.status})>"


class OrderProduct(Base):
    __tablename__ = "order_products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_size_id = Column(Integer, ForeignKey("product_sizes.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_order_product_quantity_positive'),
    )

    def __repr__(self):
        return f"<OrderProduct(id={self.id}, order_id={self.order_id}, product_size_id={self.product_size_id}, quantity={self.quantity})>"

