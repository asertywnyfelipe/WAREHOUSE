from db.db_manager import *

def handle_exception(e):
    print(f"❌ Wystąpił błąd: {e}")
#region GŁÓWNA PĘTLA APLIKACJI
def core_loop():
    while True:
        # 🔹 Przetwarzanie nowych eventów
        events = get_new_events()
        for e in events:
            process_event(e)

        # 🔹 Menu główne
        print("\n--- MENU GŁÓWNE ---")
        print("1️⃣ Dodaj typ produktu")
        print("2️⃣ Dodaj produkty do magazynu")
        print("3️⃣ Pokaż stan magazynu")
        print("4️⃣ Zarządzanie paletami")
        print("5 Zarządzanie boxami")
        print("6 Wyjście")
        print("q️⃣ Pokaż kolejkę eventów")

        choice = input("Wybierz opcję: ").strip()

        try:
            if choice == "1":
                # Dodawanie nowego typu produktu
                name = input("Nazwa produktu: ").strip()
                weight = float(input("Waga produktu (kg): "))
                max_per_box = int(input("Max produktów w boxie: "))
                add_event("ADD_PRODUCT_TYPE", payload={
                    "name": name,
                    "weight": weight,
                    "max_per_box": max_per_box
                })

            elif choice == "2":
                add_product_from_pallet_to_warehouse()

            elif choice == "3":
                # Wyświetlanie stanu magazynu
                print("\n====== STAN MAGAZYNU ======\n")

                # 1️⃣ Produkty w boksach (>0 sztuk)
                boxes = get_all_boxes()  # pełne info o wszystkich boxach
                items_in_boxes = [b for b in boxes if b["quantity"] > 0]

                print("📦 Produkty w boksach:")
                if not items_in_boxes:
                    print("  - Brak produktów w boksach.")
                else:
                    for b in items_in_boxes:
                        print(
                            f"  - {b['product_name']} | Box: {b['barcode']} "
                            f"| {b['quantity']}/{b['max_capacity']} szt."
                        )

                # 2️⃣ Palety zewnętrzne
                palets = get_external_palets()
                print("\n🪵 Palety zewnętrzne:")

                if not palets:
                    print("  - Brak palet.")
                else:
                    for p in palets:
                        barcode = p["barcode"]
                        product_id = p["product_id"]
                        quantity = p["quantity"]
                        prod = get_product_info(product_id)
                        print(f" - Paleta {barcode}: {prod['name'] if prod else 'UNKNOWN'} x {quantity}")

                # 3️⃣ Łączna liczba produktów w boksach
                total_in_boxes = sum(b["quantity"] for b in items_in_boxes)
                print(f"\n📊 Łączna liczba produktów w boksach: {total_in_boxes} szt.")

                # 4️⃣ Liczba pustych boxów
                empty_boxes = get_empty_boxes_count()
                print(f"📭 Liczba pustych boksów: {empty_boxes}")

                print("\n============================\n")

            elif choice == "4":
                manage_palets_menu()
            elif choice == "5":
                manage_boxes_menu()

            elif choice == "6":
                print("👋 Koniec programu.")
                break

            elif choice.lower() == "q":
                show_pending_events()  # teraz pokazuje tylko nieprzetworzone eventy

            else:
                print("❌ Niepoprawna opcja, spróbuj ponownie.")

        except Exception as e:
            handle_exception(e)
#endregion
#region ZARZĄDZANIE PALETAMI
def manage_palets_menu():
    while True:
        print("\n--- ZARZĄDZANIE PALETAMI ---")
        print("1️⃣ Dodaj nową paletę")
        print("2️⃣ Wyświetl dostępne palety")
        print("3️⃣ Powrót do głównego menu")

        choice = input("Wybierz opcję: ").strip()

        try:
            if choice == "1":
                print("\n--- DOSTĘPNE PRODUKTY ---")
                products = get_all_products()
                if not products:
                    print("❌ Brak produktów w bazie. Dodaj najpierw produkt typu.")
                    continue
                for i, p in enumerate(products, start=1):
                    print(f"{i}. {p['name']} (waga: {p['weight']} kg, max w boxie: {p['max_per_box']})")

                try:
                    selection = int(input("Wybierz numer produktu: "))
                    if selection < 1 or selection > len(products):
                        print("❌ Niepoprawny wybór.")
                        continue

                    chosen = products[selection - 1]
                    palet_name = input("Nazwa palety: ").strip()
                    quantity = int(input(f"Ilość produktu '{chosen['name']}' na palecie: "))

                    add_event("ADD_PALETTE", payload={
                        "product_id": chosen["id"],
                        "quantity": quantity,
                        "palet_name": palet_name
                    })
                    print(f"✅ Dodano event dodania palety '{palet_name}' z produktem '{chosen['name']}'")

                except ValueError:
                    print("⚠️ Niepoprawny wybór — wprowadź numer.")

            elif choice == "2":
                palets = get_external_palets()
                if not palets:
                    print("Brak dostępnych palet.")
                else:
                    print("\n--- DOSTĘPNE PALETY ---")
                    for p in palets:
                        barcode = p["barcode"]
                        product_id = p["product_id"]
                        quantity = p["quantity"]
                        prod = get_product_info(product_id)
                        print(f" - Paleta {barcode}: {prod['name'] if prod else 'UNKNOWN'} x {quantity}")

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
            add_products_to_stock(payload["product_id"], payload["quantity"])

        elif event["event_type"] == "ADD_PALETTE":
            add_external_palet(
                product_id=payload["product_id"],
                quantity=payload["quantity"],
                palet_name=payload.get("palet_name")
            )

        mark_event_processed(event["id"])

    except Exception as e:
        mark_event_as_failed(event["id"], str(e))
        print(f"❌ Błąd podczas przetwarzania eventu {event['event_type']}: {e}")


def add_product_from_pallet_to_warehouse():
    print("\n=== DODAWANIE PRODUKTU Z PALETY DO MAGAZYNU ===\n")

    # === 1. Pobierz palety ===
    pallets = get_external_palets()
    if not pallets:
        print("❌ Brak palet! Najpierw dodaj paletę z produktami.\n")
        return

    # === 2. Wyświetl palety ===
    print("Dostępne palety:")
    for idx, p in enumerate(pallets, start=1):
        prod = get_product_info(p["product_id"])
        prod_name = prod["name"] if prod else "UNKNOWN"
        print(f"{idx}. Paleta {p['barcode']} ({prod_name} x {p['quantity']})")

    # === 3. Wybór palety indeksem, nie ID ===
    choice = input("\nWybierz numer palety: ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(pallets)):
        print("❌ Niepoprawny numer palety.\n")
        return

    pallet = pallets[int(choice) - 1]

    # paleta ma jeden produkt
    product = get_product_info(pallet["product_id"])
    available_qty = pallet["quantity"]

    print(f"\n📦 Produkt na palecie: {product['name']} (x{available_qty})\n")

    # === 4. Ile przenieść? ===
    qty_str = input("Ile sztuk chcesz przenieść do magazynu? ").strip()
    if not qty_str.isdigit():
        print("❌ Nieprawidłowa ilość.\n")
        return

    qty_to_move = int(qty_str)
    if qty_to_move <= 0 or qty_to_move > available_qty:
        print("❌ Ilość poza zakresem.\n")
        return

    # === 5. Pobierz boxy ===
    boxes = get_all_boxes()
    if not boxes:
        print("❌ Brak boxów w magazynie! Najpierw dodaj box.\n")
        return

    print("\nDostępne boxy:")
    for b in boxes:
        prod_name = b["product_name"] if b["product_name"] else "—"
        status = "ZAPEŁNIONY" if b["quantity"] > 0 else "WOLNY"
        print(f"{b['id']}. Box {b['barcode']} [{status}] (zawiera: {prod_name})")

    # === 6. Wybór boxa ===
    box_id_str = input("\nWybierz ID boxa: ").strip()

    if not box_id_str.isdigit():
        print("❌ Nieprawidłowe ID boxa.\n")
        return

    box_id = int(box_id_str)

    # === 7. Przenieś produkty i zapisz w DB ===
    success = assign_product_from_pallet_to_box(
        pallet_id=pallet["id"],
        product_id=product["id"],
        box_id=box_id,
        quantity=qty_to_move
    )

    if success:
        print("\n✔ Produkt został przeniesiony z palety do magazynu.\n")
    else:
        print("\n❌ Błąd podczas przenoszenia produktu.\n")
#endregion
#region ZARZĄDZANIE BOXSAMI
def manage_boxes_menu():
    while True:
        print("\n--- ZARZĄDZANIE BOXSAMI ---")
        print("1️⃣ Utwórz nowy pusty box")
        print("2️⃣ Pokaż wszystkie boxy")
        print("3️⃣ Usuń pusty box")
        print("4️⃣ Wróć do głównego menu")

        choice = input("Wybierz opcję: ").strip()

        if choice == "1":
            barcode = create_box()  # tworzy pusty box
            print(f"\n📦 Utworzono pusty box {barcode}")

        elif choice == "2":
            boxes = get_all_boxes()
            if not boxes:
                print("\nBrak boxów w magazynie.")
            else:
                print("\nLista boxów:")
                for b in boxes:
                    status = "ZAPEŁNIONY" if b["quantity"] > 0 else "WOLNY"
                    prod_name = b["product_name"] or "Brak produktu"
                    print(f"{b['id']}. {b['barcode']} | {prod_name} | {b['quantity']}/{b['max_capacity']} szt. | {status} | Slot: {b['slot_id'] or 'Brak'}")

        elif choice == "3":
            boxes = get_all_boxes()
            empty_boxes = [b for b in boxes if b["quantity"] == 0]
            if not empty_boxes:
                print("\nBrak pustych boxów do usunięcia.")
                continue

            print("\nPuste boxy:")
            for b in empty_boxes:
                print(f"{b['id']}. {b['barcode']}")

            box_id = input("Wybierz ID boxa do usunięcia: ").strip()
            if not box_id.isdigit():
                print("❌ Niepoprawne ID.")
                continue

            success = delete_box(int(box_id))
            if success:
                print(f"\n🗑️ Pusty box {box_id} został usunięty.")
            else:
                print("❌ Nie można usunąć tego boxa (może nie jest pusty).")

        elif choice == "4":
            break

        else:
            print("❌ Niepoprawna opcja. Spróbuj ponownie.")
#endregion