from db.db_manager import *

def handle_exception(e):
    print(f"❌ Wystąpił błąd: {e}")

def core_loop():
    while True:
        events = get_new_events()
        for e in events:
            process_event(e)

        print("\n--- MENU GŁÓWNE ---")
        print("1️⃣ Dodaj typ produktu")
        print("2️⃣ Dodaj produkty do magazynu")
        print("3️⃣ Pokaż stan magazynu")
        print("4️⃣ Zarządzanie paletami")
        print("5️⃣ Wyjście")
        print("q️⃣ Pokaż kolejkę eventów")

        choice = input("Wybierz opcję: ").strip()

        try:
            if choice == "1":
                name = input("Nazwa produktu: ").strip()
                weight = float(input("Waga produktu (kg): "))
                max_per_box = int(input("Max produktów w boxie: "))
                add_event("ADD_PRODUCT_TYPE", payload={
                    "name": name,
                    "weight": weight,
                    "max_per_box": max_per_box
                })

            elif choice == "2":
                print("\n--- 🔍 Wyszukaj produkt ---")
                query = input("Wpisz fragment nazwy produktu: ").strip().lower()
                if not query:
                    print("❌ Nie podano nazwy, wracam do menu.")
                    continue

                matches = search_products(query)
                if not matches:
                    print("⚠️ Nie znaleziono żadnych produktów.")
                    continue

                print("\n📦 Wyniki wyszukiwania:")
                for i, p in enumerate(matches, start=1):
                    print(f"{i}. {p['name']} (waga: {p['weight']} kg, max w boxie: {p['max_per_box']})")

                try:
                    selection = int(input("\nWybierz numer produktu: "))
                    if selection < 1 or selection > len(matches):
                        print("❌ Niepoprawny wybór.")
                        continue

                    chosen = matches[selection - 1]
                    qty = int(input(f"Ile sztuk produktu '{chosen['name']}' dodać do magazynu: "))

                    add_event("ADD_PRODUCTS_TO_STOCK", payload={
                        "product_id": chosen["id"],
                        "product_name": chosen["name"],
                        "quantity": qty
                    })
                    print(f"✅ Dodano event dodania {qty} szt. produktu '{chosen['name']}'")

                except ValueError:
                    print("⚠️ Niepoprawny wybór — wprowadź numer.")
                    continue

            elif choice == "3":
                stock = get_stock_status()
                print("\n--- STAN MAGAZYNU ---")
                for item in stock:
                    print(f"{item['name']}: {item['quantity']} szt.")

            elif choice == "4":
                manage_palets_menu()

            elif choice == "5":
                print("👋 Koniec programu.")
                break

            elif choice.lower() == "q":
                show_event_queue()

            else:
                print("❌ Niepoprawna opcja, spróbuj ponownie.")

        except Exception as e:
            handle_exception(e)

def manage_palets_menu():
    while True:
        print("\n--- ZARZĄDZANIE PALETAMI ---")
        print("1️⃣ Dodaj nową paletę")
        print("2️⃣ Wyświetl dostępne palety")
        print("3️⃣ Powrót do głównego menu")

        choice = input("Wybierz opcję: ").strip()

        try:
            if choice == "1":
                palet_name = input("Nazwa palety: ").strip()
                product_name = input("Nazwa produktu: ").strip()
                quantity = int(input("Ilość produktu na palecie: "))

                if not check_product_exists(product_name):
                    print(f"❌ Produkt '{product_name}' nie istnieje w bazie. Paleta nie została dodana.")
                    continue

                add_event("ADD_PALETTE", payload={
                    "palet_name": palet_name,
                    "product_name": product_name,
                    "quantity": quantity
                })

            elif choice == "2":
                palets = get_external_palets()
                if not palets:
                    print("Brak dostępnych palet.")
                else:
                    print("\n--- DOSTĘPNE PALETY ---")
                    for p in palets:
                        print(f"- {p['name']} ({p['quantity']} produktów)")

            elif choice == "3":
                break

            else:
                print("❌ Niepoprawna opcja, spróbuj ponownie.")

        except Exception as e:
            handle_exception(e)

def process_event(event):
    try:
        payload = event.get("payload", {})

        if event["event_type"] == "ADD_PRODUCT_TYPE":
            add_product_type(
                payload["name"],
                payload["weight"],
                payload["max_per_box"]
            )

        elif event["event_type"] == "ADD_PRODUCTS_TO_STOCK":
            add_products_to_stock(payload["product_name"], payload["quantity"])

        elif event["event_type"] == "ADD_PALETTE":
            add_external_palet(payload["palet_name"], payload["product_name"], payload["quantity"])

        mark_event_processed(event["id"])

    except Exception as e:
        mark_event_as_failed(event["id"], str(e))
        print(f"❌ Błąd podczas przetwarzania eventu {event['event_type']}: {e}")

def show_event_queue():
    all_events = get_new_events()  # teraz get_new_events zwraca też przetworzone i nieprzetworzone
    if not all_events:
        print("📭 Kolejka jest pusta.")
    else:
        print("\n--- KOLEJKA ZDARZEŃ ---")
        for e in all_events:
            status = e.get("status", "NEW")
            print(f"• [{status}] {e['type']} | payload={e.get('payload', {})}")
