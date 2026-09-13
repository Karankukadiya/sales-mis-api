"""Database seeding script for Sales MIS API.

Generates realistic sales transaction records across multiple regions,
products, and dates over the past 12 months using Faker.
"""

import os
import sys
import random
import datetime as dt
from faker import Faker
from sqlalchemy.orm import Session

# Ensure app package is discoverable when executing script directly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.sale import SaleRecord
from app.repositories.sales_repository import SalesRepository

fake = Faker()
Faker.seed(42)
random.seed(42)

REGIONS = ["North", "South", "East", "West", "Central"]

PRODUCTS = [
    {"name": "Enterprise Cloud Suite", "min_price": 1200.0, "max_price": 2500.0},
    {"name": "Developer Workstation Pro", "min_price": 1600.0, "max_price": 3200.0},
    {"name": "UltraWide Curved Monitor 38\"", "min_price": 750.0, "max_price": 1150.0},
    {"name": "Mechanical Ergonomic Keyboard", "min_price": 140.0, "max_price": 240.0},
    {"name": "Noise-Canceling Headset ANC", "min_price": 180.0, "max_price": 350.0},
    {"name": "Smart Conference Hub 4K", "min_price": 850.0, "max_price": 1600.0},
    {"name": "Docking Station Thunderbolt 4", "min_price": 220.0, "max_price": 380.0},
    {"name": "Biometric Hardware Key", "min_price": 45.0, "max_price": 95.0},
]

SALESPERSONS = [
    "Sarah Jenkins",
    "Michael Chang",
    "Elena Rostova",
    "David Adebayo",
    "Priya Sharma",
    "Carlos Rodriguez",
    "Amina Al-Mansoor",
    "Liam O'Connor",
]


def generate_sales_data(num_records: int = 350) -> None:
    """Generate realistic sales records and seed into SQLite database.

    Args:
        num_records (int): Number of records to generate (default: 350).
    """
    print(f"Creating database tables on {engine.url}...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        sales_repo = SalesRepository(db)

        # Clear existing rows to allow clean reseeding
        existing_count = db.query(SaleRecord).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing records. Resetting table...")
            db.query(SaleRecord).delete()
            db.commit()

        print(f"Generating {num_records} realistic sales records...")
        today = dt.date.today()
        start_date = today - dt.timedelta(days=365)

        records_to_insert = []
        for _ in range(num_records):
            prod_info = random.choice(PRODUCTS)
            product_name = prod_info["name"]
            unit_price = round(
                random.uniform(prod_info["min_price"], prod_info["max_price"]), 2
            )

            # Weighted distribution: smaller quantities are more frequent
            quantity = random.choices(
                population=[1, 2, 3, 4, 5, 8, 10],
                weights=[35, 25, 15, 10, 8, 4, 3],
                k=1,
            )[0]

            revenue = round(quantity * unit_price, 2)
            region = random.choice(REGIONS)
            salesperson = random.choice(SALESPERSONS)

            # Random transaction date within the past 365 days
            random_days = random.randint(0, 365)
            sale_date = start_date + dt.timedelta(days=random_days)

            record = SaleRecord(
                date=sale_date,
                region=region,
                product=product_name,
                quantity=quantity,
                unit_price=unit_price,
                revenue=revenue,
                salesperson=salesperson,
            )
            records_to_insert.append(record)

        db.add_all(records_to_insert)
        db.commit()

        # Print executive summary of seeded database
        total_rev, total_units, total_tx, avg_order = sales_repo.get_total_kpis()
        top_prod = sales_repo.get_top_selling_product()

        print("\n==========================================")
        print("  Database Seeding Completed Successfully! ")
        print("==========================================")
        print(f"Total Transactions : {total_tx:,}")
        print(f"Total Units Sold   : {total_units:,}")
        print(f"Total Revenue      : ${total_rev:,.2f}")
        print(f"Average Order Value: ${avg_order:,.2f}")
        if top_prod:
            print(f"Top Product        : {top_prod['product']} (${top_prod['total_revenue']:,.2f})")
        print("==========================================")
        print("Start the API server using:")
        print("  uvicorn app.main:app --reload")
        print("And view Swagger docs at:")
        print("  http://127.0.0.1:8000/docs\n")

    except Exception as exc:
        db.rollback()
        print(f"Error during seeding: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    count = 350
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        count = int(sys.argv[1])
    generate_sales_data(count)
