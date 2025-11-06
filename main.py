
from db.db_manager import init_db
from core.core_loop import start_core
from utils.logger import log_info

if __name__ == "__main__":
    log_info("🚀 Starting warehouse core system...")
    init_db()
    start_core()

