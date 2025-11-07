import sqlite3
import math
from db.db_init import initialize_database as init_db
from db.db_manager import (
    add_product_type,
    get_product_info,
    create_box as create_new_box,
    get_stock_status,
)

DB_PATH = "warehouse.db"


def add_products_to_stock(product_name, quantity_to_add):
    """Dodaje produkty do magazynu — rozkłada je po boxach lub tworzy nowe."""
    product = get_product_info(product_name)
    if not product:
        raise ValueError(f"Produkt '{product_name}' nie istnieje w bazie.")
    product_id, max_per_box = product

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # znajdź istniejące boxy z tym produktem
    c.execute("SELECT id, barcode, quantity FROM boxes WHERE product_id = ?", (product_id,))
    existing_boxes = c.fetchall()

    remaining = quantity_to_add

    for box_id, barcode, qty in existing_boxes:
        if remaining <= 0:
            break
        free_space = max_per_box - qty
        if free_space > 0:
            to_add = min(remaining, free_space)
            new_qty = qty + to_add
            c.execute("UPDATE boxes SET quantity = ? WHERE id = ?", (new_qty, box_id))
            remaining -= to_add
            print(f"✅ Dodano {to_add} szt. do istniejącego boxa {barcode} (teraz {new_qty}/{max_per_box})")

    # jeśli zostały produkty, twórz nowe boxy
    while remaining > 0:
        to_add = min(remaining, max_per_box)
        barcode = create_new_box(product_id)
        c.execute("UPDATE boxes SET quantity = ? WHERE barcode = ?", (to_add, barcode))
        print(f"📦 Utworzono nowy box {barcode} z {to_add}/{max_per_box} szt.")
        remaining -= to_add

    conn.commit()
    conn.close()


def core_loop():
    print("=== SYSTEM MAGAZYNOWY ===")

    choice = input("Czy chcesz zainicjalizować bazę danych? (t/n): ").lower()
    if choice == "t":
        init_db()
        print("✅ Baza danych gotowa.\n")

    while True:
        print("\n1️⃣ Dodaj typ produktu")
        print("2️⃣ Dodaj produkty do magazynu")
        print("3️⃣ Pokaż stan magazynu")
        print("4️⃣ Wyjście")

        choice = input("Wybierz opcję: ")

        if choice == "1":
            name = input("Nazwa produktu: ")
            max_per_box = int(input("Max produktów w boxie: "))
            add_product_type(name, max_per_box)
            print("✅ Dodano nowy typ produktu.")
        elif choice == "2":
            product = input("Nazwa produktu: ")
            qty = int(input("Ilość do dodania: "))
            add_products_to_stock(product, qty)
        elif choice == "3":
            get_stock_status()
        elif choice == "4":
            print("👋 Koniec programu.")
            break
        else:
            print("❌ Niepoprawna opcja, spróbuj ponownie.")


if __name__ == "__main__":
    core_loop()

