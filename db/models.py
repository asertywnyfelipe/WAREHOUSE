import sqlite3

def init_db():
    conn = sqlite3.connect("warehouse.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT
    )
    """)

    cur.execute("""
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

