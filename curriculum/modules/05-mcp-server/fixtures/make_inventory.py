"""Generate deterministic inventory database with seeded randomness.

Creates inventory.sqlite3 with products, stock_levels, and suppliers tables.
Includes unicode product names and zero-stock items.
"""

import sqlite3
import random
from pathlib import Path

# Seed for reproducibility
random.seed(42)

DB_PATH = Path(__file__).parent / "inventory.sqlite3"


def create_database():
    """Create and populate the inventory database."""
    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create suppliers table
    cursor.execute(
        """
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            country TEXT,
            contact_email TEXT
        )
    """
    )

    # Create products table
    cursor.execute(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            category TEXT,
            price REAL,
            supplier_id INTEGER NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    """
    )

    # Create stock_levels table
    cursor.execute(
        """
        CREATE TABLE stock_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL UNIQUE,
            quantity_on_hand INTEGER,
            reorder_point INTEGER,
            last_updated TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """
    )

    # Insert suppliers
    suppliers = [
        ("TechCorp Industries", "USA", "sales@techcorp.com"),
        ("Global Trade Ltd", "China", "contact@globaltrade.cn"),
        ("European Parts Co.", "Germany", "info@europarts.de"),
        ("Rising Sun Supplies", "Japan", "support@risingsun.jp"),
        ("Midwest Wholesalers", "USA", "orders@midwest.com"),
    ]

    for name, country, email in suppliers:
        cursor.execute(
            "INSERT INTO suppliers (name, country, contact_email) VALUES (?, ?, ?)",
            (name, country, email),
        )

    supplier_ids = [1, 2, 3, 4, 5]

    # Insert products with unicode names
    products = [
        ("Standard Widget", "WIDGET-001", "Hardware", 9.99, 1),
        ("Premium Widget™", "WIDGET-002", "Hardware", 14.99, 1),
        ("Deluxe Gadget (型号)", "GADGET-001", "Electronics", 49.99, 2),
        ("Smart Connector™ Pro", "CONN-001", "Electronics", 29.99, 3),
        ("Industrial Belt (業務用)", "BELT-001", "Mechanical", 24.99, 2),
        ("Precision Spring", "SPRING-001", "Mechanical", 5.49, 4),
        ("LED Panel 48W (白色)", "LED-001", "Lighting", 39.99, 2),
        ("Compact Relay Module", "RELAY-001", "Electronics", 15.99, 5),
        ("Thermal Paste (導熱膏)", "PASTE-001", "Components", 8.99, 4),
        ("Water Cooling Unit (冷却)", "COOL-001", "Cooling", 89.99, 1),
        ("Industrial Cable (CAT6)", "CABLE-001", "Cabling", 12.99, 5),
        ("Replacement Filter (フィルター)", "FILTER-001", "Maintenance", 22.99, 3),
        ("Power Supply 500W", "PSU-001", "Power", 65.99, 1),
        ("Circuit Breaker 30A", "BREAKER-001", "Electrical", 34.99, 3),
        ("Mounting Bracket (金属)", "BRACKET-001", "Hardware", 7.99, 4),
    ]

    for name, sku, category, price, supplier_id in products:
        cursor.execute(
            "INSERT INTO products (name, sku, category, price, supplier_id) VALUES (?, ?, ?, ?, ?)",
            (name, sku, category, price, supplier_id),
        )

    # Insert stock levels (some with zero stock, varied quantities)
    stock_levels = [
        (1, 150, 20),
        (2, 45, 15),
        (3, 0, 10),  # Out of stock
        (4, 200, 30),
        (5, 0, 25),  # Out of stock
        (6, 500, 100),
        (7, 3, 20),  # Low stock
        (8, 120, 25),
        (9, 85, 15),
        (10, 0, 5),  # Out of stock
        (11, 250, 50),
        (12, 0, 10),  # Out of stock
        (13, 78, 20),
        (14, 1, 10),  # Very low
        (15, 350, 40),
    ]

    for product_id, quantity, reorder_point in stock_levels:
        cursor.execute(
            """
            INSERT INTO stock_levels (product_id, quantity_on_hand, reorder_point, last_updated)
            VALUES (?, ?, ?, datetime('now'))
        """,
            (product_id, quantity, reorder_point),
        )

    conn.commit()
    conn.close()

    print(f"✓ Created {DB_PATH}")
    print("  - 5 suppliers")
    print("  - 15 products (with unicode names)")
    print("  - 15 stock levels (4 items at zero stock)")


if __name__ == "__main__":
    create_database()
