"""SalesService implementing all business logic and KPI aggregation orchestration.

Ensures separation of concerns by serving as the intermediate layer between
FastAPI route controllers and the persistence SalesRepository.
"""

from datetime import date
from typing import Optional, List
from app.models.sale import SaleRecord
from app.schemas.sale import (
    SaleCreate,
    SaleUpdate,
    SalesSummaryResponse,
    RegionSummary,
    ProductSummary,
    MonthlyGrowthSummary,
)
from app.repositories.sales_repository import SalesRepository
from app.services.base import BaseService
from app.exceptions import EntityNotFoundException, BusinessRuleViolationException


class SalesService(BaseService[SalesRepository]):
    """Domain service encapsulating business rules and MIS KPI calculations."""

    def __init__(self, repository: SalesRepository) -> None:
        """Initialize SalesService with SalesRepository dependency."""
        super().__init__(repository)

    def create_sale(self, data: SaleCreate) -> SaleRecord:
        """Create and persist a new sales record with computed revenue.

        Args:
            data (SaleCreate): Validated sales input schema.

        Returns:
            SaleRecord: Persisted ORM entity.
        """
        # Business logic: calculate total revenue
        computed_revenue = round(data.quantity * data.unit_price, 2)

        record = SaleRecord(
            date=data.date,
            region=data.region,
            product=data.product,
            quantity=data.quantity,
            unit_price=data.unit_price,
            revenue=computed_revenue,
            salesperson=data.salesperson,
        )
        return self.repository.create(record)

    def get_sale(self, sale_id: int) -> SaleRecord:
        """Fetch a single sales record by ID or raise EntityNotFoundException.

        Args:
            sale_id (int): Primary key ID.

        Returns:
            SaleRecord: Found ORM entity.

        Raises:
            EntityNotFoundException: If no record matches the ID.
        """
        record = self.repository.get_by_id(sale_id)
        if not record:
            raise EntityNotFoundException(entity_name="SaleRecord", entity_id=sale_id)
        return record

    def update_sale(self, sale_id: int, data: SaleUpdate) -> SaleRecord:
        """Update an existing sales record and recompute revenue if price or quantity changes.

        Args:
            sale_id (int): Primary key ID of record to update.
            data (SaleUpdate): Fields to update.

        Returns:
            SaleRecord: Updated and refreshed ORM entity.
        """
        record = self.get_sale(sale_id)

        update_dict = data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(record, key, value)

        # Recompute revenue if quantity or unit_price was modified
        if "quantity" in update_dict or "unit_price" in update_dict:
            record.revenue = round(record.quantity * record.unit_price, 2)

        return self.repository.update(record)

    def delete_sale(self, sale_id: int) -> None:
        """Delete a sales record by ID.

        Args:
            sale_id (int): Primary key ID.

        Raises:
            EntityNotFoundException: If no record matches the ID.
        """
        record = self.get_sale(sale_id)
        self.repository.delete(record)

    def list_sales(
        self,
        region: Optional[str] = None,
        product: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[SaleRecord]:
        """List sales records with validated filters and pagination.

        Args:
            region (Optional[str]): Geographic region filter.
            product (Optional[str]): Product name filter.
            start_date (Optional[date]): Filter start date.
            end_date (Optional[date]): Filter end date.
            skip (int): Pagination offset.
            limit (int): Pagination limit.

        Returns:
            List[SaleRecord]: Matching sales records.

        Raises:
            BusinessRuleViolationException: If start_date > end_date or limit > 100.
        """
        if start_date and end_date and start_date > end_date:
            raise BusinessRuleViolationException("start_date cannot be greater than end_date")

        if limit > 100:
            raise BusinessRuleViolationException("Pagination limit cannot exceed 100 records")

        return self.repository.filter_sales(
            region=region,
            product=product,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    def get_summary_kpis(self) -> SalesSummaryResponse:
        """Aggregate high-level business intelligence KPIs for executive MIS reporting.

        Aggregates totals, regional distribution, top product, and month-over-month growth rates.

        Returns:
            SalesSummaryResponse: Formatted MIS KPI response.
        """
        # 1. Total KPI aggregates via SQL query builder
        total_rev, total_units, total_tx, avg_order = self.repository.get_total_kpis()

        # 2. Regional revenue distribution
        region_rows = self.repository.get_revenue_by_region()
        region_summaries = [
            RegionSummary(
                region=r["region"],
                total_revenue=r["total_revenue"],
                total_units=r["total_units"],
                transaction_count=r["transaction_count"],
                percentage_of_total=(
                    round((r["total_revenue"] / total_rev) * 100, 2)
                    if total_rev > 0
                    else 0.0
                ),
            )
            for r in region_rows
        ]

        # 3. Top-selling product
        top_prod_data = self.repository.get_top_selling_product()
        top_product_summary = (
            ProductSummary(**top_prod_data) if top_prod_data else None
        )

        # 4. Month-over-month revenue trend & growth rates
        monthly_rows = self.repository.get_monthly_revenue_trend()
        monthly_growth_list: List[MonthlyGrowthSummary] = []
        previous_revenue: Optional[float] = None

        for m_data in monthly_rows:
            current_rev = m_data["revenue"]
            growth_pct: Optional[float] = None

            if previous_revenue is not None:
                if previous_revenue > 0:
                    growth_pct = round(
                        ((current_rev - previous_revenue) / previous_revenue) * 100,
                        2,
                    )
                else:
                    growth_pct = 100.0 if current_rev > 0 else 0.0

            monthly_growth_list.append(
                MonthlyGrowthSummary(
                    month=m_data["month"],
                    revenue=current_rev,
                    units_sold=m_data["units_sold"],
                    growth_percentage=growth_pct,
                )
            )
            previous_revenue = current_rev

        return SalesSummaryResponse(
            total_revenue=round(total_rev, 2),
            total_units_sold=total_units,
            total_transactions=total_tx,
            average_order_value=round(avg_order, 2),
            revenue_by_region=region_summaries,
            top_selling_product=top_product_summary,
            monthly_growth=monthly_growth_list,
        )
