import sqlite3
import os
from utils.logger import log_info as log
from db.db_init import get_connection, DB_PATH


# --- EVENTS ---
def get_new_events():
    """Pobiera eventy nieprzetworzone."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, event_type, box_barcode, product_id, quantity, target_slot
        FROM events WHERE processed = 0
    """)
    events = c.fetchall()
    conn.close()
    return events


def mark_event_processed(event_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE events SET processed = 1 WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


# --- BOXES ---
def get_box_by_product(product_id):
    """Znajdź istniejący box z miejscem dla danego produktu."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT b.barcode, b.quantity, p.max_per_box
        FROM boxes b
        JOIN products p ON b.product_id = p.id
        WHERE b.product_id = ? AND b.quantity < p.max_per_box
        LIMIT 1
    """, (product_id,))
    result = c.fetchone()
    conn.close()
    return result


def create_box(product_id, quantity):
    """Utwórz nowy box z produktem."""
    conn = get_connection()
    c = conn.cursor()
    barcode = f"BOX_{product_id}_{int(os.urandom(2).hex(), 16)}"
    c.execute("""
        INSERT INTO boxes (barcode, product_id, quantity)
        VALUES (?, ?, ?)
    """, (barcode, product_id, quantity))
    conn.commit()
    conn.close()
    log(f"📦 Created new box {barcode} for product {product_id}")
    return barcode


def update_box_quantity(box_barcode, delta):
    """Zwiększ lub zmniejsz ilość produktu w boxie."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE boxes SET quantity = quantity + ? WHERE barcode = ?
    """, (delta, box_barcode))
    conn.commit()
    conn.close()
    log(f"📦 Updated box {box_barcode} by {delta} units")


def assign_box_to_slot(box_barcode, slot_id):
    """Przypisz box do slotu w magazynie."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE slots SET box_barcode = ?, status = 'BOX_WITH_PRODUCTS' WHERE id = ?
    """, (box_barcode, slot_id))
    c.execute("""
        UPDATE boxes SET slot_id = ? WHERE barcode = ?
    """, (slot_id, box_barcode))
    conn.commit()
    conn.close()
    log(f"📦 Box {box_barcode} assigned to slot {slot_id}")

def get_max_per_box_for_product(product_id):
    """Returns how many units fit in one box for given product."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT max_per_box FROM products WHERE id = ?", (product_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0


def get_free_slot():
    """Returns first empty slot available."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM slots WHERE status = 'EMPTY' LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def add_product_type(name, weight=0, max_per_box=1):
    """Dodaje produkt do tabeli products."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO products (name, weight, max_per_box)
        VALUES (?, ?, ?)
    """, (name, weight, max_per_box))
    conn.commit()
    conn.close()
    log(f"🆕 Added product {name}")

def get_product_info(product_id):
    """Zwraca informacje o produkcie po jego ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, weight, max_per_box FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    if not product:
        return None
    # Zwracamy jako słownik dla wygody
    return {
        "id": product[0],
        "name": product[1],
        "weight": product[2],
        "max_per_box": product[3]
    }

def get_stock_status():
    """Zwraca aktualny stan magazynu dla wszystkich produktów."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.name, SUM(b.quantity) as total_quantity
        FROM products p
        LEFT JOIN boxes b ON b.product_id = p.id
        GROUP BY p.id, p.name
    """)
    result = c.fetchall()
    conn.close()
    return result

