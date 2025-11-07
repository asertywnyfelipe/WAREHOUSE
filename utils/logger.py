import datetime
import os

# Ścieżka absolutna do folderu logs w katalogu projektu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

def log_info(message):
    # Upewnij się, że folder logs istnieje
    os.makedirs(LOG_DIR, exist_ok=True)

    # Pobierz aktualną datę i godzinę
    now = datetime.datetime.now()

    # Plik logu nazwany wg daty i godziny, np. logs/2025-11-06_14.log
    log_filename = now.strftime("%Y-%m-%d_%H.log")
    log_path = os.path.join(LOG_DIR, log_filename)

    # Zbuduj linię logu z timestampem
    timestamp = now.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"

    # Wypisz na konsolę i zapisz do pliku
    print(line)
    with open(log_path, "a") as f:
        f.write(line + "\n")

