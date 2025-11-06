import time
from db.db_manager import get_new_events, mark_event_as_processed, add_product
from utils.logger import log_info

def start_core():
    log_info("🚀 Warehouse core started.")
    
    while True:
        events = get_new_events()
        if events:
            for event in events:
                log_info(f"⚡ New event detected: {event['event_type']} (id={event['id']})")
                
                if event["event_type"] == "PRODUCT_ADDED":
                    # Tu można losować nazwę albo dodawać z payloadu
                    add_product("AutoProduct", event["location"])
                    log_info(f"✅ Added product at {event['location']}")
                
                mark_event_as_processed(event["id"])
        else:
            log_info("⏳ No new events...")
        
        time.sleep(20)

