import sqlite3
from utils.logger import log_info

DB_PATH = "warehouse.db"

# -----------------------------------
# 🔧 Inicjalizacja bazy danych
# -----------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        product_id INTEGER,
        location TEXT,
        processed INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()
    log_info("Database initialized successfully.")

def add_product(name, location):
    """Dodaje produkt do tabeli."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO products (name, location) VALUES (?, ?)", (name, location))
    conn.commit()
    conn.close()

def get_new_events():
    """Zwraca listę nieprzetworzonych eventów."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, event_type, product_id, location FROM events WHERE processed = 0")
    rows = c.fetchall()
    conn.close()

    events = []
    for r in rows:
        events.append({
            "id": r[0],
            "event_type": r[1],
            "product_id": r[2],
            "location": r[3]
        })
    return events

def mark_event_as_processed(event_id):
    """Ustawia processed=1 dla danego eventu."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE events SET processed = 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
