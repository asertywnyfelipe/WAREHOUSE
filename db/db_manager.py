import sqlite3
import os
import json
from utils.logger import log_info as log
from db.db_init import get_connection, DB_PATH

# --- EVENTS ---

def add_event(event_type, payload=None):
    """
    Dodaje nowy event do kolejki.
    payload: słownik z dodatkowymi danymi eventu.
    """
    payload_json = json.dumps(payload) if payload else None
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO events (event_type, payload)
        VALUES (?, ?)
    """, (event_type, payload_json))
    conn.commit()
    conn.close()
    log(f"🆕 Event added: {event_type}")


def get_new_events():
    """Pobiera nieprzetworzone eventy jako listę słowników."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, event_type, payload, created_at
        FROM events 
        WHERE processed = 0
        ORDER BY created_at ASC
    """)
    rows = c.fetchall()
    conn.close()

    events = []
    for row in rows:
        payload = json.loads(row[2]) if row[2] else {}
        events.append({
            "id": row[0],
            "event_type": row[1],
            "payload": payload,
            "created_at": row[3]
        })
    return events


def mark_event_processed(event_id):
    """Oznacza event jako przetworzony z timestampem."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE events 
        SET processed = 1, processed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (event_id,))
    conn.commit()
    conn.close()
    log(f"✅ Event {event_id} marked as processed")


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


def create_box(product_id, quantity=0):
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


# --- PRODUCTS ---

def add_product_type(name: str, weight: float, max_per_box: int):
    """Dodaje nowy typ produktu do tabeli products."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO products (name, weight, max_per_box)
            VALUES (?, ?, ?)
        """, (name, weight, max_per_box))
        conn.commit()
        log(f"🆕 Added product: {name}, weight: {weight}, max_per_box: {max_per_box}")
    except sqlite3.IntegrityError:
        log(f"⚠️ Product {name} already exists.")
    finally:
        conn.close()


def get_product_info(product_id):
    """Zwraca informacje o produkcie po jego ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, weight, max_per_box FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    if not product:
        return None
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


# --- EXTERNAL PALETS ---

def add_external_palet(name: str, quantity: int):
    """
    Dodaje nową paletę do tabeli external_palets i generuje event ADD_PALET.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO external_palets (name, quantity)
        VALUES (?, ?)
    """, (name, quantity))
    conn.commit()
    palet_id = c.lastrowid
    conn.close()
    
    log(f"📦 Dodano nową paletę {name} ({quantity} szt.)")
    
    # Dodanie eventu ADD_PALET do kolejki
    add_event("ADD_PALET", payload={"palet_id": palet_id, "name": name, "quantity": quantity})
    return palet_id


def get_external_palets():
    """
    Zwraca listę wszystkich dostępnych palet.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, quantity FROM external_palets
    """)
    palets = c.fetchall()
    conn.close()
    
    return [{"id": p[0], "name": p[1], "quantity": p[2]} for p in palets]
