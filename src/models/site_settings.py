from sqlalchemy import Column, String, Text, Integer, DateTime, func
from src.models.base import Base

class SiteSetting(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)  # JSON string
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

