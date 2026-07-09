"""
SQLite Database Module — persistent storage for the e-commerce support agent.

Tables:
  - orders: customer orders with items (JSON), status, tracking
  - shipments: carrier tracking with event history (JSON)
  - returns: return requests with RMA tracking
"""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id       TEXT PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    email          TEXT NOT NULL,
    items          TEXT NOT NULL,         -- JSON array of {product_name, sku, quantity, price}
    status         TEXT NOT NULL DEFAULT 'confirmed',
    total          REAL NOT NULL,
    created_at     TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    tracking_number TEXT
);

CREATE TABLE IF NOT EXISTS shipments (
    tracking_number TEXT PRIMARY KEY,
    carrier         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'label_created',
    estimated_delivery TEXT,
    events          TEXT NOT NULL DEFAULT '[]'  -- JSON array of {timestamp, location, description}
);

CREATE TABLE IF NOT EXISTS returns (
    rma_number     TEXT PRIMARY KEY,
    order_id       TEXT NOT NULL REFERENCES orders(order_id),
    reason         TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
    refund_amount  REAL NOT NULL,
    created_at     TEXT NOT NULL
);
"""


def init_db():
    """Create tables and seed data if empty."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)

        # Only seed if database is empty
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if count == 0:
            _seed_data(conn)

        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Seed Data — 12 orders, diverse scenarios
# ---------------------------------------------------------------------------

def _seed_data(conn: sqlite3.Connection):
    now = datetime.now()

    # --- Orders (12 orders, diverse scenarios) ---
    orders = [
        ("ORD-1001", "James Wilson", "james@example.com",
         [{"product_name": "Wireless Headphones", "sku": "SKU-501", "quantity": 1, "price": 79.99},
          {"product_name": "USB-C Cable", "sku": "SKU-102", "quantity": 2, "price": 12.99}],
         "delivered", 105.97, (now - timedelta(days=12)).isoformat(),
         "742 Evergreen Terrace, Springfield, IL 62701", "FDX-78901234"),

        ("ORD-1002", "Sarah Chen", "sarah@example.com",
         [{"product_name": "Mechanical Keyboard", "sku": "SKU-201", "quantity": 1, "price": 149.99}],
         "shipped", 149.99, (now - timedelta(days=4)).isoformat(),
         "221B Baker Street, London, NW1 6XE", "UPS-45678901"),

        ("ORD-1003", "Marcus Rivera", "marcus@example.com",
         [{"product_name": "27\" 4K Monitor", "sku": "SKU-305", "quantity": 1, "price": 499.99}],
         "confirmed", 499.99, (now - timedelta(hours=6)).isoformat(),
         "350 Fifth Avenue, New York, NY 10118", None),

        ("ORD-1004", "Emily Foster", "emily@example.com",
         [{"product_name": "Wireless Mouse", "sku": "SKU-410", "quantity": 1, "price": 49.99},
          {"product_name": "XL Mousepad", "sku": "SKU-411", "quantity": 1, "price": 19.99}],
         "cancelled", 69.98, (now - timedelta(days=3)).isoformat(),
         "1 Infinite Loop, Cupertino, CA 95014", None),

        ("ORD-1005", "David Kim", "david@example.com",
         [{"product_name": "Wireless Charger", "sku": "SKU-601", "quantity": 1, "price": 39.99}],
         "delivered", 39.99, (now - timedelta(days=5)).isoformat(),
         "1600 Amphitheatre Pkwy, Mountain View, CA 94043", "DHL-11223344"),

        ("ORD-1006", "Olivia Brown", "olivia@example.com",
         [{"product_name": "Tablet Stand", "sku": "SKU-701", "quantity": 1, "price": 29.99},
          {"product_name": "Screen Protector", "sku": "SKU-702", "quantity": 2, "price": 9.99}],
         "shipped", 49.97, (now - timedelta(days=2)).isoformat(),
         "4059 Mt Lee Dr, Hollywood, CA 90068", "UPS-99887766"),

        ("ORD-1007", "Alex Turner", "alex@example.com",
         [{"product_name": "1TB Portable SSD", "sku": "SKU-801", "quantity": 1, "price": 129.99}],
         "confirmed", 129.99, (now - timedelta(hours=2)).isoformat(),
         "10 Downing Street, London, SW1A 2AA", None),

        ("ORD-1008", "Sophia Martinez", "sophia@example.com",
         [{"product_name": "Smartwatch Pro", "sku": "SKU-901", "quantity": 1, "price": 299.99}],
         "delivered", 299.99, (now - timedelta(days=16)).isoformat(),
         "5th Ave & 59th St, New York, NY 10022", "FDX-55667788"),

        ("ORD-1009", "Daniel Park", "daniel@example.com",
         [{"product_name": "Bluetooth Speaker", "sku": "SKU-1001", "quantity": 1, "price": 89.99}],
         "delivered", 89.99, (now - timedelta(days=1)).isoformat(),
         "100 Broadway, New York, NY 10005", "DHL-99001122"),

        ("ORD-1010", "Rachel Green", "rachel@example.com",
         [{"product_name": "Laptop Sleeve", "sku": "SKU-1101", "quantity": 1, "price": 34.99}],
         "shipped", 34.99, (now - timedelta(days=6)).isoformat(),
         "90 Bedford St, New York, NY 10014", "FDX-33445566"),

        ("ORD-1011", "James Wilson", "james@example.com",
         [{"product_name": "HD Webcam", "sku": "SKU-1201", "quantity": 1, "price": 89.99}],
         "shipped", 89.99, (now - timedelta(days=1)).isoformat(),
         "742 Evergreen Terrace, Springfield, IL 62701", "UPS-11223344"),

        ("ORD-1012", "Grace Patel", "grace@example.com",
         [{"product_name": "Wireless Earbuds", "sku": "SKU-501", "quantity": 2, "price": 79.99},
          {"product_name": "Phone Case", "sku": "SKU-1301", "quantity": 1, "price": 24.99},
          {"product_name": "Car Charger", "sku": "SKU-1302", "quantity": 1, "price": 19.99}],
         "delivered", 204.96, (now - timedelta(days=7)).isoformat(),
         "555 Market St, San Francisco, CA 94105", "DHL-77889900"),
    ]

    for o in orders:
        conn.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (o[0], o[1], o[2], json.dumps(o[3], ensure_ascii=False),
             o[4], o[5], o[6], o[7], o[8]),
        )

    # --- Shipments (9 tracking records) ---
    shipments = [
        ("FDX-78901234", "FedEx", "delivered",
         (now - timedelta(days=2)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=12)).isoformat(), "location": "Chicago, IL", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=10)).isoformat(), "location": "Memphis, TN", "description": "Arrived at FedEx hub"},
             {"timestamp": (now - timedelta(days=4)).isoformat(), "location": "Springfield, IL", "description": "Out for delivery"},
             {"timestamp": (now - timedelta(days=2)).isoformat(), "location": "Springfield, IL", "description": "Delivered"},
         ]),

        ("UPS-45678901", "UPS", "in_transit",
         (now + timedelta(days=2)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=4)).isoformat(), "location": "London, UK", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=1)).isoformat(), "location": "Stansted, UK", "description": "Processing at UPS facility"},
         ]),

        ("DHL-11223344", "DHL", "delivered",
         (now - timedelta(days=3)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=5)).isoformat(), "location": "San Jose, CA", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=3)).isoformat(), "location": "Mountain View, CA", "description": "Delivered"},
         ]),

        ("UPS-99887766", "UPS", "out_for_delivery",
         now.strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=2)).isoformat(), "location": "Burbank, CA", "description": "Package picked up"},
             {"timestamp": (now - timedelta(hours=6)).isoformat(), "location": "Hollywood, CA", "description": "Out for delivery"},
         ]),

        ("FDX-55667788", "FedEx", "delivered",
         (now - timedelta(days=14)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=16)).isoformat(), "location": "Newark, NJ", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=14)).isoformat(), "location": "New York, NY", "description": "Delivered"},
         ]),

        ("DHL-99001122", "DHL", "delivered",
         (now - timedelta(days=1)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=3)).isoformat(), "location": "Jersey City, NJ", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=1)).isoformat(), "location": "New York, NY", "description": "Delivered"},
         ]),

        ("FDX-33445566", "FedEx", "in_transit",
         (now + timedelta(days=4)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=6)).isoformat(), "location": "New York, NY", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=3)).isoformat(), "location": "Paris, FR", "description": "International transit hub"},
         ]),

        ("UPS-11223344", "UPS", "in_transit",
         (now + timedelta(days=1)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=1)).isoformat(), "location": "Springfield, IL", "description": "Package picked up"},
             {"timestamp": (now - timedelta(hours=3)).isoformat(), "location": "Chicago, IL", "description": "Arrived at local facility"},
         ]),

        ("DHL-77889900", "DHL", "delivered",
         (now - timedelta(days=5)).strftime("%Y-%m-%d"),
         [
             {"timestamp": (now - timedelta(days=7)).isoformat(), "location": "Oakland, CA", "description": "Package picked up"},
             {"timestamp": (now - timedelta(days=5)).isoformat(), "location": "San Francisco, CA", "description": "Delivered"},
         ]),
    ]

    for s in shipments:
        conn.execute(
            "INSERT INTO shipments VALUES (?, ?, ?, ?, ?)",
            (s[0], s[1], s[2], s[3], json.dumps(s[4], ensure_ascii=False)),
        )

    conn.commit()
    print(f"✅ SQLite seeded: {len(orders)} orders, {len(shipments)} shipments")
