# Sales MIS REST API

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-quality REST API for managing and reporting **Sales Management Information System (MIS)** data. Designed specifically as a portfolio project showcasing modern Python backend development, Object-Oriented Programming (OOP) design patterns, clean Software Development Life Cycle (SDLC) practices, and SQL query-builder aggregations.

---

## Architecture & Design Patterns

This project follows an enterprise **Layered (N-Tier) Architecture** implementing the **Repository & Service Pattern**:

```mermaid
graph TD
    Client["Client / Frontend / BI Tool"] -->|HTTP / JSON| Router["FastAPI Routers (app/routers)"]
    Router -->|DTOs / Pydantic Models| Service["Sales Service (app/services)"]
    Service -->|Domain Entities| Repository["Sales Repository (app/repositories)"]
    Repository -->|SQLAlchemy Query Builder| Database[("SQLite Database (sales_mis.db)")]
```

### Layer Breakdown
| Layer | Directory | Responsibility | OOP / Architectural Concepts |
|---|---|---|---|
| **API / Transport** | `app/routers/` | Receives HTTP requests, validates query/path parameters, serializes responses via Pydantic DTOs. | Dependency Injection (`Depends`) |
| **Service Layer** | `app/services/` | Contains core business logic (revenue recalculation, KPI aggregation, MoM growth calculations, business rule validation). | Encapsulation, Separation of Concerns |
| **Repository Layer** | `app/repositories/`| Encapsulates all persistence logic, database session handling, and optimized SQL aggregations (`SUM`, `COUNT`, `AVG`, `GROUP BY`). | Abstraction, Generic Base Class (`BaseRepository[T]`) |
| **Domain Models** | `app/models/` | SQLAlchemy ORM declarative models mapping Python classes to relational database tables with constraints and indexes. | Inheritance (`TimestampMixin`, `Base`) |
| **Data Contracts** | `app/schemas/` | Pydantic v2 schemas for strict request validation and response formatting. | Data Transfer Objects (DTOs), Custom Field Validators |

---

## Why the Repository & Service Pattern?

In simple scripts or monolithic tutorials, database queries and business logic are frequently mixed directly inside FastAPI route functions. This API deliberately decouples them for three critical reasons:

1. **Single Responsibility Principle (SRP)**:
   - Routes only handle HTTP communication, headers, and status codes.
   - Services only handle business rules and analytics formulas.
   - Repositories only handle database queries and transactions.
2. **Testability & Mocking**:
   - The service layer can be unit-tested without any real database by mocking the repository.
   - Routes can be tested with isolated in-memory databases (`sqlite:///:memory:`) using FastAPI dependency overrides.
3. **Storage Engine Independence**:
   - If SQLite is swapped for PostgreSQL or Snowflake in the future, **zero lines of code in the route or service layers need to change** — only the repository layer changes.

---

## OOP Principles Demonstrated (Interview Cheat Sheet)

* **Encapsulation**:
  - `SalesRepository` encapsulates SQL queries and grouping logic; callers never see SQL statements or session rollback mechanics.
  - `SalesService` encapsulates business logic like revenue computation (`quantity * unit_price`) and Month-over-Month growth percentage formulas.
* **Inheritance**:
  - `SalesRepository` inherits from generic `BaseRepository[SaleRecord]`, reusing standard CRUD operations (`get_by_id`, `list_all`, `create`, `update`, `delete`).
  - `SalesService` inherits from `BaseService[SalesRepository]`.
  - `SaleRecord` uses multiple inheritance: `SaleRecord(Base, TimestampMixin)`.
* **Abstraction & Polymorphism**:
  - Generics (`TypeVar('ModelType')`) in `BaseRepository` provide a strongly-typed contract for any relational entity.
* **Dependency Injection**:
  - The repository is injected into the service, and the service is injected into the FastAPI router using `Depends(get_sales_service)`.

---

## Project Structure

```
sales-mis-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & exception handlers
│   ├── database.py              # SQLite engine, SessionLocal, get_db dependency
│   ├── exceptions.py            # Custom domain exception hierarchy (404, 400)
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py              # DeclarativeBase and TimestampMixin
│   │   └── sale.py              # SaleRecord table definition with constraints
│   ├── schemas/                 # Pydantic v2 validation models
│   │   ├── __init__.py
│   │   └── sale.py              # Request/response schemas & KPI DTOs
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py              # Generic BaseRepository[T]
│   │   └── sales_repository.py  # SalesRepository with SQL aggregates
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── base.py              # Generic BaseService
│   │   └── sales_service.py     # SalesService with KPI aggregation logic
│   └── routers/                 # FastAPI route controllers
│       ├── __init__.py
│       └── sales.py             # REST endpoints (/sales)
├── tests/                       # Pytest test suite
│   ├── __init__.py
│   ├── conftest.py              # In-memory SQLite fixtures & TestClient
│   └── test_sales.py            # 15 comprehensive unit & integration tests
├── seed.py                      # Realistic data generator using Faker (350+ rows)
├── requirements.txt             # Project dependencies
├── .gitignore                   # Ignored files (DB, cache, venv)
└── README.md                    # Comprehensive documentation
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Installation
Clone the repository and create a virtual environment:

```bash
# Clone repository
git clone https://github.com/your-username/sales-mis-api.git
cd sales-mis-api

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Seed Realistic Data
Populate the SQLite database with 350 realistic transactions spanning the past 12 months:

```bash
python seed.py
```

Output:
```text
Creating database tables on sqlite:///./sales_mis.db...
Generating 350 realistic sales records...

==========================================
  Database Seeding Completed Successfully! 
==========================================
Total Transactions : 350
Total Units Sold   : 924
Total Revenue      : $872,792.55
Average Order Value: $2,493.69
Top Product        : Developer Workstation Pro ($329,508.32)
==========================================
```

### 4. Run the API Server
Start the development server with live reload:

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

---

## Interactive API Documentation

FastAPI automatically generates interactive documentation:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Every endpoint includes detailed parameter descriptions, validation boundaries, and JSON example payloads.

---

## API Endpoints & Example Requests

### 1. Create Sales Record
`POST /sales` — Creates a new record and automatically computes `revenue = quantity * unit_price`.

```bash
curl -X POST "http://127.0.0.1:8000/sales" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-10",
    "region": "North",
    "product": "Enterprise Cloud Suite",
    "quantity": 5,
    "unit_price": 1200.0,
    "salesperson": "Jane Doe"
  }'
```

**Response (201 Created):**
```json
{
  "id": 351,
  "date": "2026-03-10",
  "region": "North",
  "product": "Enterprise Cloud Suite",
  "quantity": 5,
  "unit_price": 1200.0,
  "revenue": 6000.0,
  "salesperson": "Jane Doe",
  "created_at": "2026-03-13T08:30:00.000Z",
  "updated_at": "2026-03-13T08:30:00.000Z"
}
```

---

### 2. List & Filter Sales Records
`GET /sales` — List records with optional filtering by region, product, date bounds, and pagination.

```bash
# Filter North region with pagination
curl -X GET "http://127.0.0.1:8000/sales?region=North&skip=0&limit=5"

# Multi-attribute filter with date range
curl -X GET "http://127.0.0.1:8000/sales?product=Workstation&start_date=2026-01-01&end_date=2026-03-31"
```

---

### 3. Executive MIS KPI Summary
`GET /sales/summary` — Returns executive-level aggregated business intelligence metrics computed via SQL grouping.

```bash
curl -X GET "http://127.0.0.1:8000/sales/summary"
```

**Response (200 OK):**
```json
{
  "total_revenue": 872792.55,
  "total_units_sold": 924,
  "total_transactions": 350,
  "average_order_value": 2493.69,
  "revenue_by_region": [
    {
      "region": "West",
      "total_revenue": 210450.0,
      "total_units": 215,
      "transaction_count": 82,
      "percentage_of_total": 24.11
    },
    {
      "region": "North",
      "total_revenue": 198200.0,
      "total_units": 204,
      "transaction_count": 78,
      "percentage_of_total": 22.71
    }
  ],
  "top_selling_product": {
    "product": "Developer Workstation Pro",
    "total_revenue": 329508.32,
    "total_units": 142,
    "transaction_count": 56
  },
  "monthly_growth": [
    {
      "month": "2025-04",
      "revenue": 65420.0,
      "units_sold": 72,
      "growth_percentage": null
    },
    {
      "month": "2025-05",
      "revenue": 74150.0,
      "units_sold": 80,
      "growth_percentage": 13.34
    }
  ]
}
```

---

### 4. Fetch Record by ID
`GET /sales/{id}` — Retrieve a single record. Returns 404 if not found.

```bash
curl -X GET "http://127.0.0.1:8000/sales/1"
```

---

### 5. Update Record
`PUT /sales/{id}` — Partially or fully update fields. Automatically recalculates `revenue` if quantity or unit_price changes.

```bash
curl -X PUT "http://127.0.0.1:8000/sales/1" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 10,
    "unit_price": 1150.0
  }'
```

---

### 6. Delete Record
`DELETE /sales/{id}` — Permanently removes a sales transaction.

```bash
curl -X DELETE "http://127.0.0.1:8000/sales/1"
```
**Response: `204 No Content`**

---

## Automated Testing

The project includes 15 automated pytest tests executing against an isolated in-memory SQLite database (`sqlite:///:memory:`):

```bash
pytest -v
```

### Test Coverage Highlights:
- `test_create_sale_success`: Validates record creation and revenue computation.
- `test_create_sale_validation_negative_quantity`: Validates 422 on negative/zero quantity.
- `test_create_sale_validation_future_date`: Validates 422 on future sale date.
- `test_create_sale_validation_zero_unit_price`: Validates 422 on zero unit price.
- `test_get_sale_by_id_success` & `test_get_sale_by_id_not_found`: Validates 200 and structured 404.
- `test_list_sales_pagination`: Validates non-overlapping pagination offsets.
- `test_filter_sales_by_region` & `test_filter_sales_by_product_and_date_range`: Validates SQL filtering.
- `test_update_sale_recomputes_revenue`: Verifies business logic recalculation on update.
- `test_delete_sale_success` & `test_delete_sale_not_found`: Verifies 204 deletion and subsequent 404.
- `test_sales_summary_kpi_calculations`: Validates exact SQL aggregate metrics, regional percentages, and Month-over-Month growth formulas.
- `test_health_and_root_endpoints`: Verifies system operational status.

---

## Production Readiness & Future Improvements

1. **Database Migration to PostgreSQL**:
   - Update `DATABASE_URL` to `postgresql+psycopg2://user:password@host:5432/sales_db`.
   - Add Alembic database migrations (`alembic init alembic`) to manage schema versioning across dev/staging/prod.
2. **Authentication & Authorization**:
   - Integrate OAuth2 with JWT tokens (`PyJWT` / `passlib`) to restrict write and summary operations to authenticated analysts and managers.
3. **Caching with Redis**:
   - Cache the `GET /sales/summary` KPI response in Redis with a 15-minute TTL to reduce database load.
4. **Streaming Exports**:
   - Implement `GET /sales/export/csv` using streaming HTTP responses for large datasets without high memory consumption.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
