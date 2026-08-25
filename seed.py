import random
import sqlite3
from datetime import datetime, timedelta


DB_PATH = "report.db"

CUSTOMERS = [
    "Ali",
    "Ahmed",
    "Sara",
    "Ayesha",
    "Hamza",
    "Fatima",
    "Usman",
    "Zain",
    "Hassan",
    "Mariam",
]

PRODUCTS = [
    "Laptop Stand",
    "Wireless Mouse",
    "Keyboard",
    "USB-C Hub",
    "Webcam",
    "Headphones",
]


def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders")

    cursor.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    now = datetime.now()

    orders = []

    for _ in range(200):
        customer = random.choice(CUSTOMERS)
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5, 200), 2)

        days_ago = random.randint(0, 29)
        seconds_ago = random.randint(0, 86399)

        created_at = now - timedelta(
            days=days_ago,
            seconds=seconds_ago,
        )

        orders.append(
            (
                customer,
                product,
                amount,
                created_at.isoformat(timespec="seconds"),
            )
        )

    cursor.executemany(
        """
        INSERT INTO orders (
            customer,
            product,
            amount,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        orders,
    )

    conn.commit()

    count = cursor.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    conn.close()

    print(f"Seeded {count} orders into {DB_PATH}")


if __name__ == "__main__":
    seed_database()