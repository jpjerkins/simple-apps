"""SQLite database connection and table initialization."""

import sqlite3
from pathlib import Path

# Use /data which is mounted from persistent volume
_DB_PATH = Path("/data") / "simple-apps.db"


def _get_connection():
    """Get SQLite database connection with JSON support."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with required tables."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_id
        ON app_items(app_id)
    """)

    conn.commit()
    conn.close()


def get_connection():
    """Public API: Get database connection."""
    return _get_connection()
