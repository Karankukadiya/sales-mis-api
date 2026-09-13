import sqlite3
import pandas as pd
from datetime import datetime

# CONFIG — EDIT THIS PART 

EXCEL_FILE_PATH = "my_sales_data_1.xlsx"  
SHEET_NAME = 0                            
DATABASE_PATH = "sales_mis.db"          

COLUMN_MAP = {
    "date": "date",
    "region": "region",
    "product": "product",
    "quantity": "quantity",
    "unit_price": "unit_price",
    "salesperson": "salesperson",
}

CLEAR_EXISTING_DATA = False

def main():
    print(f"Reading '{EXCEL_FILE_PATH}'...")
    df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=SHEET_NAME)

    # Rename columns based on the mapping above
    reverse_map = {v: k for k, v in COLUMN_MAP.items()}
    df = df.rename(columns=reverse_map)

    required_cols = ["date", "region", "product", "quantity", "unit_price", "salesperson"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"\n❌ ERROR: Could not find these columns after mapping: {missing}")
        print(f"   Your Excel's actual columns are: {list(df.columns)}")
        print("   Fix the COLUMN_MAP section at the top of this script and try again.")
        return

    # Clean up the data a bit
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    now = datetime.now().isoformat()
    df["created_at"] = now
    df["updated_at"] = now

    # Basic sanity checks (same rules your API enforces)
    bad_qty = df[df["quantity"] <= 0]
    bad_price = df[df["unit_price"] <= 0]
    if len(bad_qty) > 0 or len(bad_price) > 0:
        print(f"\n⚠️  WARNING: {len(bad_qty)} rows have quantity <= 0, "
                f"{len(bad_price)} rows have unit_price <= 0.")
        print("   These rows will still be imported, but check your Excel data.")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if CLEAR_EXISTING_DATA:
        cursor.execute("DELETE FROM sales")
        print("Cleared existing records from the 'sales' table.")

    insert_cols = ["date", "region", "product", "quantity", "unit_price",
                   "revenue", "salesperson", "created_at", "updated_at"]
    rows = df[insert_cols].values.tolist()

    cursor.executemany(
        f"""INSERT INTO sales ({', '.join(insert_cols)})
            VALUES ({', '.join(['?'] * len(insert_cols))})""",
        rows,
    )
    conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    total_revenue = cursor.execute("SELECT SUM(revenue) FROM sales").fetchone()[0]
    conn.close()

    print(f"\n✅ Done! Imported {len(rows)} rows.")
    print(f"   Total records in database now: {count}")
    print(f"   Total revenue: {total_revenue:,.2f}")


if __name__ == "__main__":
    main()
