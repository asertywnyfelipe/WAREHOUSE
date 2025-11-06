import random
import time
import sqlite3
from utils.logger import log_info

DB_PATH = "warehouse.db"

def add_event(event_type, location):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO events (event_type, location, processed) VALUES (?, ?, 0)",
              (event_type, location))
    conn.commit()
    conn.close()

def simulate_events():
    names = ["Box_A", "Box_B", "Box_C"]
    locations = ["A-01-01", "B-02-03", "C-03-04"]

    while True:
        name = random.choice(names)
        loc = random.choice(locations)
        add_event("PRODUCT_ADDED", loc)
        log_info(f"📦 Event queued: add product {name} at {loc}")
        time.sleep(5)

if __name__ == "__main__":
    log_info("🧪 Starting event simulator...")
    simulate_events()

