import sqlite3
import os
import json
from utils.logger import log_info as log
from db.db_init import get_connection

# ============================================
# 🔹 Dekorator dla połączeń do DB
# ============================================
def db_connection(func):
    """Dekorator otwierający i zamykający połączenie z DB."""
    def wrapper(*args, **kwargs):
        conn = get_connection()
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            log(f"❌ DB error in {func.__name__}: {e}")
            return None
        finally:
            conn.close()
    return wrapper


# ============================================
# 🔹 EVENTY
# ============================================
@db_connection
def add_event(conn, event_type, payload=None):
    """Dodaje nowy event do kolejki."""
    if not event_type:
        log("⚠️ Próba dodania eventu bez typu.")
        return
    payload_json = json.dumps(payload) if payload else None
    conn.execute(
        "INSERT INTO events (event_type, payload) VALUES (?, ?)",
        (event_type, payload_json),
    )
    log(f"🆕 Event added: {event_type} {payload or ''}")


@db_connection
def get_new_events(conn):
    """Zwraca listę nieprzetworzonych eventów."""
    rows = conn.execute("""
        SELECT id, event_type, payload, created_at 
        FROM events 
        WHERE processed = 0
        ORDER BY created_at ASC
    """).fetchall()
    
    events = []
    for r in rows:
        payload = json.loads(r[2]) if r[2] else {}
        events.append({
            "id": r[0],
            "event_type": r[1],
            "payload": payload,
            "created_at": r[3]
        })
    return events


@db_connection
def mark_event_processed(conn, event_id):
    """Oznacza event jako przetworzony."""
    conn.execute("""
        UPDATE events 
        SET processed = 1, processed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (event_id,))
    log(f"✅ Event {event_id} marked as processed")


@db_connection
def mark_event_as_failed(conn, event_id, error_message=None):
    """Oznacza event jako nieudany (błąd w przetwarzaniu)."""
    try:
        conn.execute("""
            UPDATE events
            SET processed = -1, error_message = ?
            WHERE id = ?
        """, (error_message, event_id))
        log(f"❌ Event {event_id} marked as failed: {error_message}")
    except Exception as e:
        log(f"[ERROR] Nie udało się oznaczyć eventu {event_id} jako nieudanego: {e}")


def show_pending_events():
    """Wyświetla aktualnie nieprzetworzone eventy."""
    events = get_new_events()
    if not events:
        print("Brak oczekujących eventów ✅")
        return
    print("\n--- 📋 Oczekujące eventy ---")
    for ev in events:
        print(f"#{ev['id']} | {ev['event_type']} | payload: {ev['payload']} | {ev['created_at']}")
    print("------------------------------\n")


# ============================================
# 🔹 PRODUKTY
# ============================================
@db_connection
def add_product_type(conn, name: str, weight: float, max_per_box: int):
    """Dodaje nowy typ produktu."""
    if not name or weight <= 0 or max_per_box <= 0:
        log("⚠️ Nieprawidłowe dane produktu.")
        return
    try:
        conn.execute("""
            INSERT INTO products (name, weight, max_per_box)
            VALUES (?, ?, ?)
        """, (name, weight, max_per_box))
        log(f"🆕 Added product: {name}, weight={weight}, max_per_box={max_per_box}")
    except sqlite3.IntegrityError:
        log(f"⚠️ Product {name} already exists.")


@db_connection
def get_product_info(conn, product_id):
    """Zwraca informacje o produkcie po ID."""
    c = conn.execute("SELECT id, name, weight, max_per_box FROM products WHERE id = ?", (product_id,))
    row = c.fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "weight": row[2], "max_per_box": row[3]}


@db_connection
def get_product_by_name(conn, name):
    """Zwraca produkt po nazwie (pomocne przy walidacji palety)."""
    c = conn.execute("SELECT id, name, weight, max_per_box FROM products WHERE name = ?", (name,))
    row = c.fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "weight": row[2], "max_per_box": row[3]}


@db_connection
def get_stock_status(conn):
    """Zwraca stan magazynu."""
    rows = conn.execute("""
        SELECT p.id, p.name, IFNULL(SUM(b.quantity), 0) as total_quantity
        FROM products p
        LEFT JOIN boxes b ON b.product_id = p.id
        GROUP BY p.id, p.name
    """).fetchall()
    return [{"id": r[0], "name": r[1], "quantity": r[2]} for r in rows]


@db_connection
def check_product_exists(conn, product_name):
    """Sprawdza, czy produkt istnieje w bazie."""
    try:
        cursor = conn.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        log(f"[ERROR] Błąd przy sprawdzaniu produktu '{product_name}': {e}")
        return False


# ============================================
# 🔹 BOXY
# ============================================
@db_connection
def get_box_by_product(conn, product_id):
    """Zwraca istniejący box z wolnym miejscem."""
    c = conn.execute("""
        SELECT b.barcode, b.quantity, p.max_per_box
        FROM boxes b
        JOIN products p ON b.product_id = p.id
        WHERE b.product_id = ? AND b.quantity < p.max_per_box
        LIMIT 1
    """, (product_id,))
    row = c.fetchone()
    if not row:
        return None
    return {"barcode": row[0], "quantity": row[1], "max_per_box": row[2]}


@db_connection
def create_box(conn, product_id, quantity=0):
    """Tworzy nowy box."""
    barcode = f"BOX_{product_id}_{int.from_bytes(os.urandom(2), 'big')}"
    conn.execute("""
        INSERT INTO boxes (barcode, product_id, quantity)
        VALUES (?, ?, ?)
    """, (barcode, product_id, quantity))
    log(f"📦 Created new box {barcode} for product {product_id}")
    return barcode


@db_connection
def update_box_quantity(conn, box_barcode, delta):
    """Aktualizuje ilość w boxie."""
    conn.execute("UPDATE boxes SET quantity = quantity + ? WHERE barcode = ?", (delta, box_barcode))
    log(f"📦 Updated box {box_barcode} by {delta} units")


@db_connection
def get_max_per_box_for_product(conn, product_id):
    """Zwraca maksymalną ilość produktu w boxie."""
    row = conn.execute("SELECT max_per_box FROM products WHERE id = ?", (product_id,)).fetchone()
    return row[0] if row else 0


@db_connection
def get_free_slot(conn):
    """Zwraca pierwszy pusty slot."""
    row = conn.execute("SELECT id FROM slots WHERE status = 'EMPTY' ORDER BY id ASC LIMIT 1").fetchone()
    return row[0] if row else None


@db_connection
def assign_box_to_slot(conn, box_barcode, slot_id):
    """Przypisuje box do slotu."""
    conn.execute("UPDATE slots SET box_barcode = ?, status = 'BOX_WITH_PRODUCTS' WHERE id = ?", (box_barcode, slot_id))
    conn.execute("UPDATE boxes SET slot_id = ? WHERE barcode = ?", (slot_id, box_barcode))
    log(f"📦 Box {box_barcode} assigned to slot {slot_id}")


# ============================================
# 🔹 PALETY ZEWNĘTRZNE
# ============================================
@db_connection
def add_external_palet(conn, product_name: str, quantity: int):
    """
    Dodaje nową paletę, jeśli produkt istnieje w bazie.
    Jeśli produkt nie istnieje → paleta oznaczona jako błędna.
    """
    if not product_name or quantity <= 0:
        log("⚠️ Nieprawidłowe dane palety.")
        return None

    # Walidacja produktu
    product = get_product_by_name(product_name)
    if not product:
        log(f"❌ Nie dodano palety: produkt '{product_name}' nie istnieje w bazie.")
        return None

    conn.execute("""
        INSERT INTO external_palets (name, quantity)
        VALUES (?, ?)
    """, (product_name, quantity))
    palet_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    log(f"📦 Dodano nową paletę {product_name} ({quantity} szt.)")
    return palet_id


@db_connection
def get_external_palets(conn):
    """Zwraca wszystkie dostępne palety."""
    rows = conn.execute("SELECT id, name, quantity FROM external_palets").fetchall()
    return [{"id": r[0], "name": r[1], "quantity": r[2]} for r in rows]


@db_connection
def search_products(conn, query: str):
    """Zwraca listę produktów, których nazwa zawiera podany fragment."""
    query = f"%{query.lower()}%"
    rows = conn.execute("""
        SELECT id, name, weight, max_per_box
        FROM products
        WHERE LOWER(name) LIKE ?
        ORDER BY name ASC
    """, (query,)).fetchall()

    return [
        {"id": r[0], "name": r[1], "weight": r[2], "max_per_box": r[3]}
        for r in rows
    ]

@db_connection
def add_products_to_stock(conn, product_name: str, quantity: int):
    """
    Dodaje produkty do magazynu.
    Tworzy nowe boxy lub uzupełnia istniejące do max_per_box.
    """
    if quantity <= 0:
        log("⚠️ Niepoprawna ilość produktów.")
        return False

    # Sprawdzenie, czy produkt istnieje
    product = get_product_by_name(product_name)
    if not product:
        log(f"❌ Produkt '{product_name}' nie istnieje w bazie.")
        return False

    remaining = quantity
    product_id = product["id"]
    max_per_box = product["max_per_box"]

    # Najpierw próbujemy uzupełnić istniejące boxy
    while remaining > 0:
        box = get_box_by_product(product_id)
        if box:
            addable = min(max_per_box - box["quantity"], remaining)
            update_box_quantity(box["barcode"], addable)
            remaining -= addable
        else:
            # Tworzymy nowy box
            add_qty = min(max_per_box, remaining)
            create_box(product_id, add_qty)
            remaining -= add_qty

    log(f"✅ Dodano {quantity} szt. produktu '{product_name}' do magazynu.")
    return True


# ============================================
# 🔹 Eksport publicznych funkcji
# ============================================
__all__ = [
    "add_event", "get_new_events", "mark_event_processed", "mark_event_as_failed",
    "show_pending_events",
    "add_product_type", "get_product_info", "get_product_by_name", "get_stock_status",
    "check_product_exists",
    "get_box_by_product", "create_box", "update_box_quantity", "get_max_per_box_for_product",
    "get_free_slot", "assign_box_to_slot",
    "add_external_palet", "get_external_palets", "search_products", "add_products_to_stock"
]
