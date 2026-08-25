import sqlite3


DB_PATH = "report.db"


def getReportData():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Total number of orders
    total_orders = cursor.execute(
        """
        SELECT COUNT(*) AS total_orders
        FROM orders
        """
    ).fetchone()["total_orders"]

    # 2. Total revenue and average order amount
    revenue_data = cursor.execute(
        """
        SELECT
            SUM(amount) AS total_revenue,
            AVG(amount) AS average_order_amount
        FROM orders
        """
    ).fetchone()

    # 3. Top 5 products by revenue
    top_products = cursor.execute(
        """
        SELECT
            product,
            SUM(amount) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
        """
    ).fetchall()

    # 4. Orders per day for the last 7 days
    orders_per_day = cursor.execute(
        """
        SELECT
            DATE(created_at) AS date,
            COUNT(*) AS orders
        FROM orders
        WHERE DATE(created_at) >= DATE('now', '-6 days')
        GROUP BY DATE(created_at)
        ORDER BY date ASC
        """
    ).fetchall()

    conn.close()

    return {
        "summary": {
            "total_orders": total_orders,
            "total_revenue": round(revenue_data["total_revenue"], 2),
            "average_order_amount": round(
                revenue_data["average_order_amount"], 2
            ),
        },
        "top_products": [
            {
                "product": row["product"],
                "revenue": round(row["revenue"], 2),
            }
            for row in top_products
        ],
        "orders_per_day": [
            {
                "date": row["date"],
                "orders": row["orders"],
            }
            for row in orders_per_day
        ],
    }