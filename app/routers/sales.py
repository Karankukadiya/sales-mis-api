"""FastAPI router endpoints for Sales MIS resources.

Implements RESTful HTTP controllers that strictly delegate all persistence and business
logic to the SalesService layer via Dependency Injection.
"""

import datetime as dt
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.sales_repository import SalesRepository
from app.services.sales_service import SalesService
from app.schemas.sale import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    SalesSummaryResponse,
)

router = APIRouter(prefix="/sales", tags=["Sales MIS"])


def get_sales_service(db: Session = Depends(get_db)) -> SalesService:
    """Dependency provider creating an instance of SalesService with active DB session.

    Demonstrates Dependency Injection: routes declare dependencies via FastAPI,
    making them decoupled and easily mockable in unit and integration tests.
    """
    repository = SalesRepository(db)
    return SalesService(repository)


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sales record",
    description="Validates incoming sales transaction payload, automatically computes revenue, and persists the record.",
)
def create_sale(
    payload: SaleCreate,
    service: SalesService = Depends(get_sales_service),
) -> SaleResponse:
    """Create a new sales transaction record."""
    return service.create_sale(payload)


@router.get(
    "",
    response_model=List[SaleResponse],
    status_code=status.HTTP_200_OK,
    summary="List and filter sales records",
    description="Retrieve a paginated list of sales records with optional filtering by region, product, and date bounds.",
)
def list_sales(
    region: Optional[str] = Query(None, description="Filter by geographic region"),
    product: Optional[str] = Query(None, description="Filter by product name"),
    start_date: Optional[dt.date] = Query(None, description="Filter sales on or after this date (YYYY-MM-DD)"),
    end_date: Optional[dt.date] = Query(None, description="Filter sales on or before this date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return (1-100)"),
    service: SalesService = Depends(get_sales_service),
) -> List[SaleResponse]:
    """Retrieve filtered and paginated sales records."""
    return service.list_sales(
        region=region,
        product=product,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/summary",
    response_model=SalesSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get executive MIS KPI summary",
    description="Computes aggregate KPIs including total revenue, units sold, average order value, regional share, top-selling product, and month-over-month growth.",
)
def get_sales_summary(
    service: SalesService = Depends(get_sales_service),
) -> SalesSummaryResponse:
    """Retrieve executive MIS KPI metrics and trend aggregations."""
    return service.get_summary_kpis()


@router.get(
    "/{id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sale record by ID",
    description="Retrieve detailed attributes for a single sales transaction by primary key ID.",
)
def get_sale_by_id(
    id: int = Path(..., ge=1, description="Primary key ID of the sales record"),
    service: SalesService = Depends(get_sales_service),
) -> SaleResponse:
    """Fetch single sales record by ID."""
    return service.get_sale(id)


@router.put(
    "/{id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update sale record",
    description="Partially or fully update sales attributes. Revenue is automatically recalculated if quantity or unit price changes.",
)
def update_sale(
    payload: SaleUpdate,
    id: int = Path(..., ge=1, description="Primary key ID of the sales record to update"),
    service: SalesService = Depends(get_sales_service),
) -> SaleResponse:
    """Update existing sales record."""
    return service.update_sale(id, payload)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete sale record",
    description="Permanently delete a sales transaction record from the database.",
)
def delete_sale(
    id: int = Path(..., ge=1, description="Primary key ID of the sales record to delete"),
    service: SalesService = Depends(get_sales_service),
) -> Response:
    """Delete sales record by ID."""
    service.delete_sale(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
