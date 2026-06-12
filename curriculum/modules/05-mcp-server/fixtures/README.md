# M5 Fixtures Documentation

## Inventory Database

A mock inventory management database demonstrating MCP resource design with realistic business data.

### Files

- **make_inventory.py** — Generator script that creates the database with seeded randomness
- **inventory.sqlite3** — Generated SQLite database (created by running make_inventory.py)

### Database Schema

#### suppliers Table
```sql
id (INTEGER PRIMARY KEY)
name (TEXT NOT NULL UNIQUE)  -- e.g., "TechCorp Industries"
country (TEXT)               -- e.g., "USA"
contact_email (TEXT)         -- e.g., "sales@techcorp.com"
```

**Records:** 5 suppliers spanning multiple countries

#### products Table
```sql
id (INTEGER PRIMARY KEY)
name (TEXT NOT NULL)         -- Product name, includes unicode (e.g., "LED Panel 48W (白色)", "Gadget (型号)")
sku (TEXT NOT NULL UNIQUE)   -- Stock keeping unit (e.g., "WIDGET-001")
category (TEXT)              -- e.g., "Hardware", "Electronics"
price (REAL)                 -- Unit price in USD
supplier_id (INTEGER NOT NULL) -- Foreign key to suppliers
```

**Records:** 15 products including unicode names (Japanese, Chinese characters, trademark symbols)

**Notable products:**
- "Deluxe Gadget (型号)" — Zero stock
- "Industrial Belt (業務用)" — Zero stock  
- "Water Cooling Unit (冷却)" — Zero stock
- "Replacement Filter (フィルター)" — Zero stock
- "LED Panel 48W (白色)" — Very low stock (3 units)
- "Standard Widget" — Normal inventory (150 units)

#### stock_levels Table
```sql
id (INTEGER PRIMARY KEY)
product_id (INTEGER NOT NULL UNIQUE) -- Foreign key to products
quantity_on_hand (INTEGER)           -- Current inventory count
reorder_point (INTEGER)              -- Threshold for reordering
last_updated (TEXT)                  -- ISO-8601 timestamp
```

**Records:** 15 stock levels
- **Zero-stock items:** 4 products at quantity_on_hand = 0
- **Low stock:** 1 product below reorder point
- **Normal stock:** Mix of 50-500 units
- **High stock:** Some items at 500+ units

### Data Characteristics

- **Seeded randomness:** All data generated with `random.seed(42)` for reproducibility
- **Unicode support:** Product names in Japanese, Chinese, and trademark symbols test encoding
- **Zero-stock items:** Test the distinction between empty results and errors (empty-result ≠ error probe)
- **International scope:** Suppliers from USA, China, Germany, Japan
- **Realistic quantities:** Mix of bulk items (belt), electronics, components
- **Deterministic:** Running make_inventory.py again produces identical database

### Generation

```bash
python3 make_inventory.py
```

Creates `inventory.sqlite3` in the same directory. Safe to delete and regenerate.

### Testing Notes

- No external dependencies (uses stdlib sqlite3)
- All timestamps are current (generated with `datetime('now')`)
- Designed to test MCP resource description quality as a routing mechanism
- Empty results (zero stock) should return empty list, not error
- Unicode handling tests encoding and parsing
