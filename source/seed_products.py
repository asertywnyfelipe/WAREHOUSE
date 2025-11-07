import os
import sqlite3

# Absolute path to the main database file (in project root)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "warehouse.db")

def seed_sample_products():
    print("🚀 Seeding sample products...")
    print(f"📂 Using database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if 'products' table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    table_exists = c.fetchone()
    if not table_exists:
        print("❌ Table 'products' not found. Make sure you initialized the database first.")
        conn.close()
        return

    # Check if products are already seeded
    c.execute("SELECT COUNT(*) FROM products")
    count = c.fetchone()[0]
    if count > 0:
        print(f"ℹ️ {count} products already exist. Seeding skipped.")
        conn.close()
        return

    # Sample products
    sample_products = [
        ("Cookie Box", 0.3, 30),
        ("Screw Pack", 0.5, 50),
        ("Patelnia Pro", 2.2, 5),
        ("Wrench Set", 1.5, 10),
        ("Toy Car", 0.7, 15),
        ("Laptop Sleeve", 0.9, 8),
        ("Glass Bottle", 0.4, 20),
        ("Keyboard", 1.1, 6),
        ("LED Bulb Pack", 0.2, 40),
        ("Cable Roll", 1.0, 12),
    ]

    # Insert sample products
    c.executemany(
        "INSERT INTO products (name, weight, max_per_box) VALUES (?, ?, ?)",
        sample_products,
    )
    conn.commit()
    conn.close()

    print("✅ Sample products added successfully!")


if __name__ == "__main__":
    seed_sample_products()

