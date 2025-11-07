import sqlite3
import os

DB_PATH = "warehouse.db"

def get_connection():
    """Returns connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """Creates all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # --- PRODUCTS ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            weight REAL DEFAULT 0,
            max_per_box INTEGER DEFAULT 1
        )
    """)

    # --- BOXES ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS boxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL UNIQUE,
            product_id INTEGER,
            quantity INTEGER DEFAULT 0,
            max_capacity INTEGER DEFAULT 0,
            slot_id TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # --- SLOTS ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id TEXT PRIMARY KEY,            -- e.g. "A0105"
            aisle TEXT NOT NULL,
            col INTEGER NOT NULL,
            slot INTEGER NOT NULL,
            status TEXT DEFAULT 'EMPTY',    -- EMPTY | BOX_EMPTY | BOX_WITH_PRODUCTS
            box_barcode TEXT,
            FOREIGN KEY (box_barcode) REFERENCES boxes (barcode)
        )
    """)

  # --- EXTERNAL_PALETS ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS external_palets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # --- EVENTS ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload TEXT, 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed INTEGER DEFAULT 0,
            processed_at DATETIME
        )
    """)

    conn.commit()
    conn.close()


def generate_slots(num_aisles=5, num_columns=10, slots_per_column=20):
    """Generates the full warehouse slot grid, only if it's empty."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM slots")
    count = c.fetchone()[0]

    if count > 0:
        print("✅ Slots already exist. Skipping generation.")
        conn.close()
        return

    print("🧱 Generating warehouse slots...")

    for a in range(num_aisles):
        aisle_letter = chr(65 + a)  # A, B, C, D, E...
        for col in range(1, num_columns + 1):
            for s in range(1, slots_per_column + 1):
                slot_id = f"{aisle_letter}{col:02d}{s:02d}"
                c.execute("""
                    INSERT INTO slots (id, aisle, col, slot, status)
                    VALUES (?, ?, ?, ?, 'EMPTY')
                """, (slot_id, aisle_letter, col, s))

    conn.commit()
    conn.close()
    print("✅ Warehouse slots successfully generated!")


def reset_database():
    """Clears all tables — used to reset the simulation."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM events")
    c.execute("DELETE FROM boxes")
    c.execute("DELETE FROM slots")
    c.execute("DELETE FROM products")
    conn.commit()
    conn.close()


