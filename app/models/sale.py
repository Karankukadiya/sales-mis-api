"""SaleRecord SQLAlchemy ORM model.

Defines the database schema for the sales table with proper constraints,
indexes, and audit timestamp tracking via TimestampMixin.
"""

from sqlalchemy import Column, Integer, String, Float, Date, CheckConstraint
from app.database import Base
from app.models.base import TimestampMixin


class SaleRecord(Base, TimestampMixin):
    """ORM model representing a single sales transaction in the MIS.

    Attributes:
        id (int): Primary key autoincrement ID.
        date (date): Date of the transaction (cannot be future date).
        region (str): Geographical sales territory (e.g., North, South, East, West).
        product (str): Name or SKU of the sold product.
        quantity (int): Number of units sold (must be > 0).
        unit_price (float): Price per unit in USD/currency (must be > 0).
        revenue (float): Total monetary value of sale (quantity * unit_price).
        salesperson (str): Full name of the sales representative.
        created_at (datetime): Audit timestamp when record was created.
        updated_at (datetime): Audit timestamp when record was last updated.
    """

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    product = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    salesperson = Column(String(100), nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("unit_price > 0", name="check_positive_unit_price"),
        CheckConstraint("revenue >= 0", name="check_non_negative_revenue"),
    )

    def __repr__(self) -> str:
        """Return human-readable string representation of the model."""
        return (
            f"<SaleRecord(id={self.id}, date={self.date}, "
            f"region='{self.region}', product='{self.product}', "
            f"revenue={self.revenue})>"
        )
