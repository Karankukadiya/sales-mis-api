"""Main FastAPI application entrypoint for Sales MIS REST API.

Configures application lifecycle, global exception handling, CORS/middleware,
and mounts API routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.models import SaleRecord  # Ensures model is registered with Base.metadata
from app.routers import sales_router
from app.exceptions import EntityNotFoundException, BusinessRuleViolationException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events.

    Creates database tables automatically on application startup.
    """
    # Create database schema on startup if it doesn't already exist
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sales MIS API",
    description=(
        "**Sales Management Information System (MIS) REST API**\n\n"
        "A layered, production-grade REST API demonstrating SDLC best practices, "
        "Domain-Driven Repository & Service patterns, SQLAlchemy ORM with SQLite, "
        "and SQL aggregate business intelligence reporting.\n\n"
        "### Key Capabilities:\n"
        "- **CRUD Operations**: Full sales transaction lifecycle.\n"
        "- **Multi-parameter Filtering**: Filter by region, product, and chronological date bounds.\n"
        "- **Executive KPI Analytics**: Server-side SQL aggregations for revenue share, "
        "top products, and month-over-month growth."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Sales MIS",
            "description": "Operations for managing sales transactions and executive KPI aggregations.",
        },
        {
            "name": "System",
            "description": "Operational and health check endpoints.",
        },
    ],
)


@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
    """Transform EntityNotFoundException into standard HTTP 404 response."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "NOT_FOUND",
            "detail": exc.message,
            "entity": exc.entity_name,
            "id": exc.entity_id,
        },
    )


@app.exception_handler(BusinessRuleViolationException)
async def business_rule_violation_handler(
    request: Request, exc: BusinessRuleViolationException
) -> JSONResponse:
    """Transform BusinessRuleViolationException into standard HTTP 400 response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "BAD_REQUEST",
            "detail": exc.message,
        },
    )


# Mount feature routers
app.include_router(sales_router)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    description="Returns the operational status of the service.",
)
def health_check() -> dict:
    """Check API operational status."""
    return {
        "status": "healthy",
        "service": "Sales MIS API",
        "version": "1.0.0",
    }


@app.get(
    "/",
    tags=["System"],
    summary="API Root Information",
    description="Provides quick landing information and links to interactive OpenAPI documentation.",
)
def root_info() -> dict:
    """Provide root welcome message with documentation link."""
    return {
        "message": "Welcome to the Sales MIS REST API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
