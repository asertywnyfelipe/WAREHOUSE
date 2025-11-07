import datetime
import os

# Używamy aktualnego katalogu roboczego
BASE_DIR = os.getcwd()
LOG_DIR = os.path.join(BASE_DIR, "logs")

def log_info(message):
    os.makedirs(LOG_DIR, exist_ok=True)
    
    now = datetime.datetime.now()
    log_filename = now.strftime("%Y-%m-%d_%H.log")
    log_path = os.path.join(LOG_DIR, log_filename)
    
    timestamp = now.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"
    
    # DEBUG
    print(f"[LOG] {line} -> {log_path}")
    
    # Zapis do pliku i wypis na konsolę
    print(line)
    with open(log_path, "a") as f:
        f.write(line + "\n")
