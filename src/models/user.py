from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import declarative_base
from src.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(15), nullable=True)
    avatar = Column(String(500), nullable=True)
    address = Column(String(200), nullable=True)
    city = Column(String(255), nullable=True)
    postal_code = Column(String(10), nullable=True)
    country = Column(String(50), default="Russia")
    email_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"