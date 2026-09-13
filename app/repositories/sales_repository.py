"""SalesRepository encapsulating all database queries for sales records.

Implements specialized query-builder filtering and SQL aggregation queries
for MIS business analytics and KPIs.
"""

from datetime import date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc
from app.models.sale import SaleRecord
from app.repositories.base import BaseRepository


class SalesRepository(BaseRepository[SaleRecord]):
    """Repository subclass tailored for SaleRecord entities and MIS reporting.

    Demonstrates OOP Inheritance by extending BaseRepository with domain-specific
    filtering logic and high-performance SQL aggregate computations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize SalesRepository bound to SaleRecord model."""
        super().__init__(db, SaleRecord)

    def filter_sales(
        self,
        region: Optional[str] = None,
        product: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[SaleRecord]:
        """Query sales records with optional multi-attribute filters and pagination.

        Args:
            region (Optional[str]): Exact or partial region name filter.
            product (Optional[str]): Exact or partial product name filter.
            start_date (Optional[date]): Filter records on or after this date.
            end_date (Optional[date]): Filter records on or before this date.
            skip (int): Pagination offset.
            limit (int): Pagination record count limit.

        Returns:
            List[SaleRecord]: Filtered list of sales records.
        """
        stmt = select(SaleRecord)

        if region:
            stmt = stmt.where(SaleRecord.region.ilike(f"%{region.strip()}%"))
        if product:
            stmt = stmt.where(SaleRecord.product.ilike(f"%{product.strip()}%"))
        if start_date:
            stmt = stmt.where(SaleRecord.date >= start_date)
        if end_date:
            stmt = stmt.where(SaleRecord.date <= end_date)

        stmt = stmt.order_by(SaleRecord.date.desc(), SaleRecord.id.desc())
        stmt = stmt.offset(skip).limit(limit)

        return list(self.db.scalars(stmt).all())

    def get_total_kpis(self) -> Tuple[float, int, int, float]:
        """Compute aggregate total revenue, total units, transaction count, and average order value.

        Uses database-level SQL aggregate functions (SUM, COUNT, AVG) instead of
        loading rows into memory.

        Returns:
            Tuple[float, int, int, float]: (total_revenue, total_units, total_transactions, avg_order_value)
        """
        stmt = select(
            func.coalesce(func.sum(SaleRecord.revenue), 0.0).label("total_revenue"),
            func.coalesce(func.sum(SaleRecord.quantity), 0).label("total_units"),
            func.count(SaleRecord.id).label("total_transactions"),
            func.coalesce(func.avg(SaleRecord.revenue), 0.0).label("avg_order_value"),
        )
        row = self.db.execute(stmt).one()
        return (
            float(row.total_revenue),
            int(row.total_units),
            int(row.total_transactions),
            float(row.avg_order_value),
        )

    def get_revenue_by_region(self) -> List[Dict[str, Any]]:
        """Compute revenue, unit sales, and transaction count grouped by region.

        Executes SQL GROUP BY region, sorted by total revenue in descending order.

        Returns:
            List[Dict[str, Any]]: Aggregated metrics per region.
        """
        stmt = (
            select(
                SaleRecord.region,
                func.coalesce(func.sum(SaleRecord.revenue), 0.0).label("total_revenue"),
                func.coalesce(func.sum(SaleRecord.quantity), 0).label("total_units"),
                func.count(SaleRecord.id).label("transaction_count"),
            )
            .group_by(SaleRecord.region)
            .order_by(desc("total_revenue"))
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "region": row.region,
                "total_revenue": float(row.total_revenue),
                "total_units": int(row.total_units),
                "transaction_count": int(row.transaction_count),
            }
            for row in rows
        ]

    def get_top_selling_product(self) -> Optional[Dict[str, Any]]:
        """Identify the highest revenue generating product.

        Executes SQL GROUP BY product ORDER BY sum(revenue) DESC LIMIT 1.

        Returns:
            Optional[Dict[str, Any]]: Top product metrics or None if no sales exist.
        """
        stmt = (
            select(
                SaleRecord.product,
                func.coalesce(func.sum(SaleRecord.revenue), 0.0).label("total_revenue"),
                func.coalesce(func.sum(SaleRecord.quantity), 0).label("total_units"),
                func.count(SaleRecord.id).label("transaction_count"),
            )
            .group_by(SaleRecord.product)
            .order_by(desc("total_revenue"))
            .limit(1)
        )
        row = self.db.execute(stmt).first()
        if not row:
            return None
        return {
            "product": row.product,
            "total_revenue": float(row.total_revenue),
            "total_units": int(row.total_units),
            "transaction_count": int(row.transaction_count),
        }

    def get_monthly_revenue_trend(self) -> List[Dict[str, Any]]:
        """Aggregate revenue and units sold chronologically by calendar month (YYYY-MM).

        Uses SQLite strftime('%Y-%m', date) for server-side SQL date truncation.

        Returns:
            List[Dict[str, Any]]: Chronological monthly aggregates.
        """
        month_col = func.strftime("%Y-%m", SaleRecord.date).label("month")
        stmt = (
            select(
                month_col,
                func.coalesce(func.sum(SaleRecord.revenue), 0.0).label("revenue"),
                func.coalesce(func.sum(SaleRecord.quantity), 0).label("units_sold"),
            )
            .group_by(month_col)
            .order_by(asc(month_col))
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "month": row.month,
                "revenue": float(row.revenue),
                "units_sold": int(row.units_sold),
            }
            for row in rows
        ]
