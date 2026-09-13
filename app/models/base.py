"""Base model and mixins for SQLAlchemy ORM models.

Demonstrates OOP principles through inheritance and reusable model mixins.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from app.database import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at audit timestamps.

    Demonstrates the OOP Mixin pattern: encapsulates audit timestamp behavior
    that can be inherited by any database model requiring change tracking.
    """

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
