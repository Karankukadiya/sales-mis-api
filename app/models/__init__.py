"""Models package exporting all ORM entities."""

from app.models.base import TimestampMixin
from app.models.sale import SaleRecord
from app.database import Base

__all__ = ["Base", "TimestampMixin", "SaleRecord"]
