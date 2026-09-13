"""Comprehensive test suite for Sales MIS REST API.

Covers CRUD lifecycle, input validations, filtering, pagination,
KPI aggregation queries, error handling, and edge cases.
"""

import datetime as dt
from fastapi.testclient import TestClient


def test_create_sale_success(client: TestClient) -> None:
    """Test creating a sales record successfully with auto-computed revenue."""
    payload = {
        "date": "2026-03-01",
        "region": "North",
        "product": "Enterprise Cloud Suite",
        "quantity": 5,
        "unit_price": 250.0,
        "salesperson": "Jane Doe",
    }
    response = client.post("/sales", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["region"] == "North"
    assert data["product"] == "Enterprise Cloud Suite"
    assert data["quantity"] == 5
    assert data["unit_price"] == 250.0
    assert data["revenue"] == 1250.0  # 5 * 250.0
    assert data["salesperson"] == "Jane Doe"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_sale_validation_negative_quantity(client: TestClient) -> None:
    """Test that creating a record with non-positive quantity fails validation (422)."""
    payload = {
        "date": "2026-03-01",
        "region": "East",
        "product": "Laptop Stand",
        "quantity": -2,
        "unit_price": 45.0,
        "salesperson": "John Smith",
    }
    response = client.post("/sales", json=payload)
    assert response.status_code == 422


def test_create_sale_validation_future_date(client: TestClient) -> None:
    """Test that creating a record with a future date fails validation (422)."""
    future_date = (dt.date.today() + dt.timedelta(days=10)).isoformat()
    payload = {
        "date": future_date,
        "region": "West",
        "product": "Monitor 4K",
        "quantity": 1,
        "unit_price": 400.0,
        "salesperson": "Alice Johnson",
    }
    response = client.post("/sales", json=payload)
    assert response.status_code == 422
    assert "future" in response.text.lower()


def test_create_sale_validation_zero_unit_price(client: TestClient) -> None:
    """Test that unit_price <= 0 fails validation (422)."""
    payload = {
        "date": "2026-03-01",
        "region": "West",
        "product": "Monitor 4K",
        "quantity": 1,
        "unit_price": 0.0,
        "salesperson": "Alice Johnson",
    }
    response = client.post("/sales", json=payload)
    assert response.status_code == 422


def test_get_sale_by_id_success(client: TestClient) -> None:
    """Test retrieving an existing sales record by ID (200)."""
    create_res = client.post(
        "/sales",
        json={
            "date": "2026-02-15",
            "region": "South",
            "product": "Mechanical Keyboard",
            "quantity": 3,
            "unit_price": 120.0,
            "salesperson": "Bob Lee",
        },
    )
    sale_id = create_res.json()["id"]

    get_res = client.get(f"/sales/{sale_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == sale_id
    assert data["product"] == "Mechanical Keyboard"
    assert data["revenue"] == 360.0


def test_get_sale_by_id_not_found(client: TestClient) -> None:
    """Test fetching a non-existent sale ID returns 404 with structured error."""
    response = client.get("/sales/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NOT_FOUND"
    assert "999999" in data["detail"]


def test_list_sales_pagination(client: TestClient) -> None:
    """Test listing sales records with skip and limit pagination parameters."""
    for i in range(12):
        client.post(
            "/sales",
            json={
                "date": "2026-01-10",
                "region": "Central",
                "product": f"Product-{i}",
                "quantity": 1,
                "unit_price": 50.0,
                "salesperson": "Agent X",
            },
        )

    # Page 1: 5 records
    res_p1 = client.get("/sales?skip=0&limit=5")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert len(data_p1) == 5

    # Page 2: 5 records
    res_p2 = client.get("/sales?skip=5&limit=5")
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert len(data_p2) == 5

    # Verify no overlap between page 1 and page 2 IDs
    ids_p1 = {item["id"] for item in data_p1}
    ids_p2 = {item["id"] for item in data_p2}
    assert ids_p1.isdisjoint(ids_p2)


def test_filter_sales_by_region(client: TestClient) -> None:
    """Test filtering records by region query parameter."""
    client.post(
        "/sales",
        json={
            "date": "2026-02-01",
            "region": "North",
            "product": "Widget A",
            "quantity": 1,
            "unit_price": 100.0,
            "salesperson": "Alice",
        },
    )
    client.post(
        "/sales",
        json={
            "date": "2026-02-02",
            "region": "South",
            "product": "Widget B",
            "quantity": 2,
            "unit_price": 150.0,
            "salesperson": "Bob",
        },
    )

    res = client.get("/sales?region=North")
    assert res.status_code == 200
    records = res.json()
    assert len(records) >= 1
    assert all(r["region"] == "North" for r in records)


def test_filter_sales_by_product_and_date_range(client: TestClient) -> None:
    """Test multi-attribute filtering by product and start_date/end_date bounds."""
    client.post(
        "/sales",
        json={
            "date": "2026-01-15",
            "region": "East",
            "product": "Cloud Service",
            "quantity": 1,
            "unit_price": 500.0,
            "salesperson": "Charlie",
        },
    )
    client.post(
        "/sales",
        json={
            "date": "2026-02-15",
            "region": "East",
            "product": "Cloud Service",
            "quantity": 2,
            "unit_price": 500.0,
            "salesperson": "Charlie",
        },
    )
    client.post(
        "/sales",
        json={
            "date": "2026-03-05",
            "region": "East",
            "product": "Cloud Service",
            "quantity": 1,
            "unit_price": 500.0,
            "salesperson": "Charlie",
        },
    )

    # Query only February
    res = client.get("/sales?product=Cloud Service&start_date=2026-02-01&end_date=2026-02-28")
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 1
    assert records[0]["date"] == "2026-02-15"


def test_update_sale_recomputes_revenue(client: TestClient) -> None:
    """Test updating quantity and price recalculates the revenue automatically."""
    create_res = client.post(
        "/sales",
        json={
            "date": "2026-02-10",
            "region": "West",
            "product": "Tablet",
            "quantity": 2,
            "unit_price": 300.0,
            "salesperson": "Diana",
        },
    )
    sale_id = create_res.json()["id"]
    assert create_res.json()["revenue"] == 600.0

    # Update quantity from 2 to 5
    update_res = client.put(f"/sales/{sale_id}", json={"quantity": 5})
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["quantity"] == 5
    assert updated_data["unit_price"] == 300.0
    assert updated_data["revenue"] == 1500.0  # 5 * 300.0


def test_update_sale_not_found(client: TestClient) -> None:
    """Test updating a non-existent sale ID returns 404."""
    response = client.put("/sales/888888", json={"quantity": 10})
    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"


def test_delete_sale_success(client: TestClient) -> None:
    """Test deleting an existing sales record (204) and verifying subsequent 404."""
    create_res = client.post(
        "/sales",
        json={
            "date": "2026-01-20",
            "region": "Central",
            "product": "Desk Pad",
            "quantity": 4,
            "unit_price": 25.0,
            "salesperson": "Evan",
        },
    )
    sale_id = create_res.json()["id"]

    del_res = client.delete(f"/sales/{sale_id}")
    assert del_res.status_code == 204

    # Verify subsequent GET returns 404
    get_res = client.get(f"/sales/{sale_id}")
    assert get_res.status_code == 404


def test_delete_sale_not_found(client: TestClient) -> None:
    """Test deleting a non-existent record returns 404."""
    response = client.delete("/sales/777777")
    assert response.status_code == 404


def test_sales_summary_kpi_calculations(client: TestClient) -> None:
    """Test executive KPI summary endpoint validates aggregate SQL calculations."""
    # Month 1: 2026-01
    client.post(
        "/sales",
        json={
            "date": "2026-01-10",
            "region": "North",
            "product": "Laptop",
            "quantity": 2,
            "unit_price": 1000.0,
            "salesperson": "Alice",
        },
    )  # rev: 2000.0
    client.post(
        "/sales",
        json={
            "date": "2026-01-20",
            "region": "South",
            "product": "Headphones",
            "quantity": 5,
            "unit_price": 200.0,
            "salesperson": "Bob",
        },
    )  # rev: 1000.0
    # Month 1 total = 3000.0

    # Month 2: 2026-02
    client.post(
        "/sales",
        json={
            "date": "2026-02-15",
            "region": "North",
            "product": "Laptop",
            "quantity": 3,
            "unit_price": 1000.0,
            "salesperson": "Alice",
        },
    )  # rev: 3000.0
    # Month 2 total = 3000.0 -> MoM growth = 0.0%

    # Month 3: 2026-03
    client.post(
        "/sales",
        json={
            "date": "2026-03-01",
            "region": "North",
            "product": "Laptop",
            "quantity": 6,
            "unit_price": 1000.0,
            "salesperson": "Alice",
        },
    )  # rev: 6000.0
    # Month 3 total = 6000.0 -> MoM growth = +100.0%

    res = client.get("/sales/summary")
    assert res.status_code == 200
    summary = res.json()

    # Total KPIs
    assert summary["total_revenue"] == 12000.0
    assert summary["total_units_sold"] == 16  # 2 + 5 + 3 + 6
    assert summary["total_transactions"] == 4
    assert summary["average_order_value"] == 3000.0  # 12000 / 4

    # Top selling product
    assert summary["top_selling_product"] is not None
    assert summary["top_selling_product"]["product"] == "Laptop"
    assert summary["top_selling_product"]["total_revenue"] == 11000.0

    # Regional distribution
    regions = {r["region"]: r for r in summary["revenue_by_region"]}
    assert "North" in regions
    assert "South" in regions
    assert regions["North"]["total_revenue"] == 11000.0
    assert regions["South"]["total_revenue"] == 1000.0
    assert regions["North"]["percentage_of_total"] == 91.67
    assert regions["South"]["percentage_of_total"] == 8.33

    # Monthly growth
    months = summary["monthly_growth"]
    assert len(months) == 3
    assert months[0]["month"] == "2026-01"
    assert months[0]["growth_percentage"] is None  # Baseline
    assert months[1]["month"] == "2026-02"
    assert months[1]["growth_percentage"] == 0.0
    assert months[2]["month"] == "2026-03"
    assert months[2]["growth_percentage"] == 100.0


def test_health_and_root_endpoints(client: TestClient) -> None:
    """Test health check and root landing endpoints return 200 OK."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["docs"] == "/docs"
