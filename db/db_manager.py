import sqlite3
import os
import json
from utils.logger import log_info as log
from db.db_init import get_connection
#region Dekorator
# ============================================
# 🔹 Dekorator dla połączeń do DB
# ============================================
def db_connection(func):
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
#endregion
#region EVENTY
# ============================================
# 🔹 EVENTY
# ============================================
@db_connection
def add_event(conn, event_type, payload=None):
    payload_json = json.dumps(payload) if payload else None
    conn.execute(
        "INSERT INTO events (event_type, payload) VALUES (?, ?)",
        (event_type, payload_json),
    )
    log(f"🆕 Event added: {event_type} {payload or ''}")

@db_connection
def get_new_events(conn):
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
    conn.execute("""
        UPDATE events 
        SET processed = 1, processed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (event_id,))
    log(f"✅ Event {event_id} marked as processed")

@db_connection
def mark_event_as_failed(conn, event_id, error_message=None):
    conn.execute("""
        UPDATE events
        SET processed = -1, error_message = ?
        WHERE id = ?
    """, (error_message, event_id))
    log(f"❌ Event {event_id} marked as failed: {error_message}")

def show_pending_events():
    events = get_new_events()
    if not events:
        print("Brak oczekujących eventów ✅")
        return
    print("\n--- 📋 Oczekujące eventy ---")
    for ev in events:
        print(f"#{ev['id']} | {ev['event_type']} | payload: {ev['payload']} | {ev['created_at']}")
    print("------------------------------\n")
#endregion
#region PRODUKTY
# ============================================
# 🔹 PRODUKTY
# ============================================
@db_connection
def add_product_type(conn, name: str, weight: float, max_per_box: int):
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
    row = conn.execute("SELECT id, name, weight, max_per_box FROM products WHERE id = ?", (product_id,)).fetchone()
    return {"id": row[0], "name": row[1], "weight": row[2], "max_per_box": row[3]} if row else None

@db_connection
def get_product_by_name(conn, name):
    row = conn.execute("SELECT id, name, weight, max_per_box FROM products WHERE name = ?", (name,)).fetchone()
    return {"id": row[0], "name": row[1], "weight": row[2], "max_per_box": row[3]} if row else None

@db_connection
def check_product_exists(conn, product_name):
    row = conn.execute("SELECT id FROM products WHERE name = ?", (product_name,)).fetchone()
    return row is not None

@db_connection
def get_all_products(conn):
    """Zwraca wszystkie produkty w bazie."""
    rows = conn.execute("SELECT id, name, weight, max_per_box FROM products ORDER BY name ASC").fetchall()
    return [
        {"id": r[0], "name": r[1], "weight": r[2], "max_per_box": r[3]}
        for r in rows
    ]
#endregion
#region BOXY
# ============================================
# 🔹 BOXY
# ============================================
@db_connection
def create_box(conn, product_id=None, quantity=0):
    """Tworzy nowy box z opcjonalnym produktem."""
    barcode = f"BOX_{int.from_bytes(os.urandom(2), 'big')}"
    max_capacity = 0

    if product_id:
        product = get_product_info(product_id)
        if not product:
            raise ValueError("Produkt nie istnieje")
        max_capacity = product["max_per_box"]

    conn.execute("""
        INSERT INTO boxes (barcode, product_id, quantity, max_capacity)
        VALUES (?, ?, ?, ?)
    """, (barcode, product_id, quantity, max_capacity))

    log(f"📦 Box created: {barcode} product={product_id} qty={quantity}")
    return barcode


@db_connection
def delete_box(conn, box_id):
    """Usuwa box tylko jeśli jest pusty i bez produktu."""
    row = conn.execute("SELECT quantity, product_id FROM boxes WHERE id=?", (box_id,)).fetchone()
    if not row:
        return False

    quantity, product_id = row
    if quantity != 0 or product_id is not None:
        return False

    conn.execute("DELETE FROM boxes WHERE id=?", (box_id,))
    log(f"🗑 Deleted empty box ID={box_id}")
    return True


@db_connection
def get_box(conn, box_id):
    """Zwraca dane jednego boxa."""
    r = conn.execute("""
        SELECT id, barcode, product_id, quantity, max_capacity, slot_id
        FROM boxes WHERE id=?
    """, (box_id,)).fetchone()

    if not r:
        return None

    return {
        "id": r[0],
        "barcode": r[1],
        "product_id": r[2],
        "quantity": r[3],
        "max_capacity": r[4],
        "slot_id": r[5]
    }


@db_connection
def get_box_by_barcode(conn, barcode):
    """Pobiera box po kodzie."""
    r = conn.execute("""
        SELECT id, barcode, product_id, quantity, max_capacity, slot_id
        FROM boxes WHERE barcode=?
    """, (barcode,)).fetchone()

    if not r:
        return None

    return {
        "id": r[0],
        "barcode": r[1],
        "product_id": r[2],
        "quantity": r[3],
        "max_capacity": r[4],
        "slot_id": r[5]
    }


@db_connection
def get_all_boxes(conn):
    """Lista wszystkich boxów."""
    rows = conn.execute("""
        SELECT b.id, b.barcode, b.product_id, p.name AS product_name,
               b.quantity, b.max_capacity, b.slot_id
        FROM boxes b
        LEFT JOIN products p ON p.id = b.product_id
        ORDER BY b.id ASC
    """).fetchall()

    return [
        {
            "id": r[0],
            "barcode": r[1],
            "product_id": r[2],
            "product_name": r[3],
            "quantity": r[4],
            "max_capacity": r[5],
            "slot_id": r[6]
        }
        for r in rows
    ]


@db_connection
def get_empty_boxes(conn):
    """Zwraca wszystkie puste boxy."""
    rows = conn.execute("""
        SELECT id, barcode FROM boxes WHERE quantity=0 OR product_id IS NULL
    """).fetchall()

    return [{"id": r[0], "barcode": r[1]} for r in rows]


@db_connection
def update_box_quantity(conn, box_barcode, delta, product_id=None):
    """Dodaje/odejmuje ilość. Jeśli box pusty, ustawia produkt."""
    if product_id:
        product = get_product_info(product_id)
        if not product:
            raise ValueError("Invalid product_id")

        conn.execute("""
            UPDATE boxes
            SET product_id=?, max_capacity=?
            WHERE barcode=? AND (product_id IS NULL OR quantity=0)
        """, (product_id, product["max_per_box"], box_barcode))

    conn.execute("""
        UPDATE boxes SET quantity = quantity + ? WHERE barcode=?
    """, (delta, box_barcode))

    log(f"📦 Updated box {box_barcode}: +{delta} units")


@db_connection
def set_box_slot(conn, box_id, slot_id):
    """Przypisuje box do slotu."""
    conn.execute("UPDATE boxes SET slot_id=? WHERE id=?", (slot_id, box_id))
    log(f"📦 Box {box_id} → Slot {slot_id}")


@db_connection
def clear_box_slot(conn, box_id):
    """Usuwa przypisanie boxa do slotu."""
    conn.execute("UPDATE boxes SET slot_id=NULL WHERE id=?", (box_id,))
    log(f"📦 Box {box_id} unassigned from slot")


@db_connection
def find_box_with_free_space(conn, product_id):
    """Znajduje box z miejscem dla danego produktu."""
    row = conn.execute("""
        SELECT id, barcode, quantity, max_capacity
        FROM boxes
        WHERE product_id=? AND quantity < max_capacity
        ORDER BY id ASC
        LIMIT 1
    """, (product_id,)).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "barcode": row[1],
        "quantity": row[2],
        "max_capacity": row[3]
    }
@db_connection
def get_box_by_product(conn, product_id):
    """Zwraca istniejący box z wolnym miejscem."""
    row = conn.execute("""
        SELECT barcode, quantity, max_capacity
        FROM boxes
        WHERE product_id = ? AND quantity < max_capacity
        LIMIT 1
    """, (product_id,)).fetchone()
    return {"barcode": row[0], "quantity": row[1], "max_capacity": row[2]} if row else None


def create_empty_box():
    """Alias wygodny w użyciu — tworzy pusty box."""
    return create_box(None, 0)

@db_connection
def get_empty_boxes_count(conn):
    """Zwraca liczbę pustych boxów."""
    row = conn.execute("""
        SELECT COUNT(*) FROM boxes WHERE quantity = 0 OR product_id IS NULL
    """).fetchone()
    return row[0] if row else 0

@db_connection
def assign_product_from_pallet_to_box(conn, pallet_id, product_id, box_id, quantity, slot_id=None):
    """Przenosi produkty z palety do boxa i ustawia slot w magazynie."""
    # === 1. Pobierz paletę ===
    pallet = conn.execute("SELECT id, product_id, quantity, barcode FROM external_palets WHERE id=?", (pallet_id,)).fetchone()
    if not pallet:
        return False

    pallet_id_db, p_id, p_qty, pallet_barcode = pallet
    if p_qty < quantity:
        return False  # za mało na palecie

    # === 2. Pobierz box ===
    box = conn.execute("SELECT barcode, product_id, quantity, max_capacity FROM boxes WHERE id=?", (box_id,)).fetchone()
    if not box:
        return False

    box_barcode, b_product_id, b_qty, b_cap = box

    # === 3. Pobierz info o produkcie ===
    product = get_product_info(product_id)
    if not product:
        return False

    # === 4. Sprawdzenie i aktualizacja boxa ===
    if b_product_id is None:
        # box pusty → przypisujemy produkt
        max_cap = product["max_per_box"]
        if quantity > max_cap:
            return False
        conn.execute("""
            UPDATE boxes
            SET product_id=?, max_capacity=?, quantity=?, slot_id=?
            WHERE id=?
        """, (product_id, max_cap, quantity, slot_id, box_id))
    else:
        # box zawiera już produkt
        if b_product_id != product_id or (b_qty + quantity > b_cap):
            return False
        conn.execute("""
            UPDATE boxes
            SET quantity = quantity + ?, slot_id=?
            WHERE id=?
        """, (quantity, slot_id, box_id))

    # === 5. Zmniejszamy ilość na palecie ===
    new_qty = p_qty - quantity
    if new_qty <= 0:
        conn.execute("DELETE FROM external_palets WHERE id=?", (pallet_id,))
    else:
        conn.execute("UPDATE external_palets SET quantity=? WHERE id=?", (new_qty, pallet_id))

    log(f"📦 Przeniesiono {quantity} x {product['name']} z palety {pallet_barcode} do boxa {box_barcode} (slot: {slot_id or 'Brak'})")
    return True


#endregion
#region PALETY ZEWNĘTRZNE
# ============================================
# 🔹 PALETY ZEWNĘTRZNE
# ============================================

@db_connection
def add_external_palet(conn, product_id: int, quantity: int, palet_name: str):
    try:
        conn.execute("""
            INSERT INTO external_palets (barcode, product_id, quantity)
            VALUES (?, ?, ?)
        """, (palet_name, product_id, quantity))
        log(f"🆕 Added external pallet: {palet_name} (product {product_id}, qty={quantity})")
    except sqlite3.IntegrityError:
        log(f"⚠️ External pallet '{palet_name}' already exists.")

@db_connection
def get_external_palets(conn):
    """Return external pallets as list of dicts: {id, barcode, product_id, quantity}."""
    # ustawienie row_factory nie jest potrzebne w dekoratorze — mapujemy ręcznie
    rows = conn.execute("SELECT id, barcode, product_id, quantity FROM external_palets ORDER BY id ASC").fetchall()
    return [
        {"id": r[0], "barcode": r[1], "product_id": r[2], "quantity": r[3]}
        for r in rows
    ]
@db_connection
def get_total_on_palets(conn, product_id):
    row = conn.execute("SELECT IFNULL(SUM(quantity),0) FROM external_palets WHERE product_id = ?", (product_id,)).fetchone()
    return row[0] if row else 0

@db_connection
def take_products_from_palets(conn, product_id: int, quantity: int):
    total_taken = 0
    needed = quantity
    rows = conn.execute("""
        SELECT id, quantity FROM external_palets
        WHERE product_id = ? ORDER BY created_at ASC
    """, (product_id,)).fetchall()
    for r in rows:
        if needed <= 0:
            break
        palet_id, palet_qty = r
        take = min(palet_qty, needed)
        new_qty = palet_qty - take
        if new_qty > 0:
            conn.execute("UPDATE external_palets SET quantity=? WHERE id=?", (new_qty, palet_id))
        else:
            conn.execute("DELETE FROM external_palets WHERE id=?", (palet_id,))
        total_taken += take
        needed -= take
    if total_taken < quantity:
        log(f"⚠️ Nie udało się pobrać całej ilości: chciałeś {quantity}, pobrano {total_taken}")
    return total_taken

# ============================================
# 🔹 DODAWANIE PRODUKTÓW DO MAGAZYNU
# ============================================
def add_products_to_stock(product_id: int, quantity: int):
    available = get_total_on_palets(product_id)
    if quantity > available:
        log(f"❌ Za mało produktów na paletach: dostępne {available}, próbujesz dodać {quantity}")
        return
    product_info = get_product_info(product_id)
    max_per_box = product_info['max_per_box']
    boxes_needed = (quantity + max_per_box - 1) // max_per_box
    empty_boxes = get_empty_boxes_count()
    if boxes_needed > empty_boxes:
        log(f"❌ Za mało pustych boxów: potrzebne {boxes_needed}, dostępne {empty_boxes}")
        return
    taken = take_products_from_palets(product_id, quantity)
    remaining = taken
    while remaining > 0:
        box = get_box_by_product(product_id)
        if box:
            box_barcode = box['barcode']
        else:
            box_barcode = create_box()  # pusty box
        box_qty = min(remaining, max_per_box)
        update_box_quantity(box_barcode, box_qty, product_id=product_id)
        remaining -= box_qty

# ============================================
# 🔹 WYŚWIETLANIE STANU MAGAZYNU
# ============================================
def show_stock():
    boxes = get_all_boxes()
    palets = get_external_palets()

    print("\n====== STAN MAGAZYNU ======\n")

    # Produkty w boksach
    boxes_with_products = [b for b in boxes if b['current_quantity'] > 0 and b['product_id']]
    if not boxes_with_products:
        print("📦 Produkty w boksach:\n  - Brak produktów w boksach.")
    else:
        print("📦 Produkty w boksach:")
        for b in boxes_with_products:
            free_space = b['max_capacity'] - b['current_quantity']
            print(f"  - {b['barcode']} | {b['product_name']} | {b['current_quantity']}/{b['max_capacity']} szt. | wolne: {free_space}")

    # Palety zewnętrzne
    if not palets:
        print("\n🪵 Palety zewnętrzne:\n  - Brak palet.")
    else:
        print("\n🪵 Palety zewnętrzne:")
        for p in palets:
            print(f"  - {p['name']} | {p['product_name']} | {p['quantity']} szt.")

    total_in_boxes = sum(b['current_quantity'] for b in boxes_with_products)
    empty_boxes = sum(1 for b in boxes if not b['product_id'] or b['current_quantity'] == 0)
    print(f"\n📊 Łączna liczba produktów w boksach: {total_in_boxes} szt.")
    print(f"📭 Liczba pustych boksów: {empty_boxes}")

    print("\n============================\n")
#endregion


# ============================================
# 🔹 EXPORT
# ============================================
__all__ = [
    "add_event","get_new_events","mark_event_processed","mark_event_as_failed","show_pending_events",
    "add_product_type","get_product_info","get_product_by_name","check_product_exists",
    "create_box","get_box_by_product","update_box_quantity","get_all_boxes","get_empty_boxes_count",
    "add_external_palet","get_external_palets","get_total_on_palets","take_products_from_palets",
    "add_products_to_stock","show_stock", "get_all_products", "delete_box", "get_box", "get_box_by_barcode",
    "set_box_slot", "clear_box_slot", "assign_product_from_pallet_to_box"
]
