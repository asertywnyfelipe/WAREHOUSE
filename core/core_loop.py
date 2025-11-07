import sqlite3
from utils.error_handler import handle_exception
from db.db_init import initialize_database as init_db
from db.db_manager import (
    add_product_type,
    get_product_info,
    create_box as create_new_box,
    get_stock_status,
    add_event,
    get_new_events,
    mark_event_processed,
    get_external_palets,
)
from utils.logger import log_info as log

# --- Funkcja obsługi pojedynczego eventu ---
def process_event(event):
    event_type = event["event_type"]
    payload = event.get("payload", {})
    try:
        if event_type == "ADD_PRODUCT_TYPE":
            add_product_type(payload["name"], payload["weight"], payload["max_per_box"])
            log(f"✅ Event executed: Added product {payload['name']}")
        elif event_type == "ADD_PRODUCTS_TO_STOCK":
            from core.stock import add_products_to_stock  # import dynamiczny
            add_products_to_stock(payload["product_name"], payload["quantity"])
            log(f"✅ Event executed: Added {payload['quantity']} {payload['product_name']} to stock")
        elif event_type == "ADD_PALETTE":
            from core.manage_palets import create_external_palet
            create_external_palet(payload["palet_name"])
            log(f"✅ Event executed: Added external palet {payload['palet_name']}")
        else:
            log(f"⚠️ Unknown event type: {event_type}")
    except Exception as e:
        handle_exception(e)
    finally:
        mark_event_processed(event["id"])


# --- Core loop z eventami ---
def core_loop():
    print("=== SYSTEM MAGAZYNOWY ===")

    choice = input("Czy chcesz zainicjalizować bazę danych? (t/n): ").lower()
    if choice == "t":
        init_db()
        print("✅ Baza danych gotowa.\n")

    while True:
        # przetwarzamy wszystkie nieprzetworzone eventy
        events = get_new_events()
        for e in events:
            process_event(e)

        # menu główne
        print("\n1️⃣ Dodaj typ produktu")
        print("2️⃣ Dodaj produkty do magazynu")
        print("3️⃣ Pokaż stan magazynu")
        print("4️⃣ Zarządzanie paletami")
        print("5️⃣ Wyjście")

        choice = input("Wybierz opcję: ")

        try:
            if choice == "1":
                name = input("Nazwa produktu: ")
                weight = float(input("Waga produktu (kg): "))
                max_per_box = int(input("Max produktów w boxie: "))
                add_event("ADD_PRODUCT_TYPE", payload={
                    "name": name,
                    "weight": weight,
                    "max_per_box": max_per_box
                })

            elif choice == "2":
                product = input("Nazwa produktu: ")
                qty = int(input("Ilość do dodania: "))
                add_event("ADD_PRODUCTS_TO_STOCK", payload={
                    "product_name": product,
                    "quantity": qty
                })

            elif choice == "3":
                stock = get_stock_status()
                for p_id, name, total in stock:
                    print(f"{name}: {total} szt.")

            elif choice == "4":
                manage_palets_menu()

            elif choice == "5":
                print("👋 Koniec programu.")
                break

            else:
                print("❌ Niepoprawna opcja, spróbuj ponownie.")
        except Exception as e:
            handle_exception(e)


# --- Podmenu do zarządzania paletami ---
def manage_palets_menu():
    while True:
        print("\n--- ZARZĄDZANIE PALETAMI ---")
        print("1️⃣ Dodaj nową paletę")
        print("2️⃣ Wyświetl dostępne palety")
        print("3️⃣ Powrót do głównego menu")

        choice = input("Wybierz opcję: ")

        try:
            if choice == "1":
                palet_name = input("Nazwa palety: ")
                add_event("ADD_PALETTE", payload={"palet_name": palet_name})

            elif choice == "2":
                palets = get_external_palets()
                if not palets:
                    print("Brak dostępnych palet.")
                else:
                    for p in palets:
                        print(f"- {p['name']} ({p['quantity']} produktów)")

            elif choice == "3":
                break

            else:
                print("❌ Niepoprawna opcja, spróbuj ponownie.")
        except Exception as e:
            handle_exception(e)


if __name__ == "__main__":
    core_loop()
