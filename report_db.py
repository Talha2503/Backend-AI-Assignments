import sqlite3
from datetime import datetime, timezone


DB_PATH = "report.db"


def init_report_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_report(created_at):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        INSERT INTO reports (path, created_at)
        VALUES (?, ?)
        """,
        ("", created_at),
    )

    report_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return report_id


def update_report_path(report_id, path):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        UPDATE reports
        SET path = ?
        WHERE id = ?
        """,
        (path, report_id),
    )

    conn.commit()
    conn.close()


def get_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT id, path, created_at
        FROM reports
        WHERE id = ?
        """,
        (report_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def get_todays_report():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    today = datetime.now(timezone.utc).date().isoformat()

    row = conn.execute(
        """
        SELECT id, path, created_at
        FROM reports
        WHERE created_at LIKE ?
        AND path != ''
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"{today}%",),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def delete_report(report_id):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        DELETE FROM reports
        WHERE id = ?
        """,
        (report_id,),
    )

    conn.commit()
    conn.close()