"""Per-app SQLite database utility with generic JSON blob storage.

Each app gets its own SQLite file.  Data is stored as a JSON blob in the
``data`` column so the schema stays stable regardless of app-specific fields.

Usage (from an app router)::

    from pathlib import Path
    from backend.platform.app_db import AppDatabase

    _db = AppDatabase(Path(__file__).parent / "data" / "myapp.db")
    _db.init()  # idempotent – safe to call on every module load
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class AppDatabase:
    """Manages one SQLite file with a generic items table.

    The table schema is intentionally minimal::

        CREATE TABLE items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            data       TEXT    NOT NULL,          -- JSON blob
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    All app-specific fields live inside the ``data`` JSON column.  This mirrors
    the legacy platform design and avoids per-app schema migrations.

    Args:
        db_path: Absolute or relative path to the ``.db`` file.  The parent
                 directory is created automatically on :meth:`init`.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Create the database file and tables if they do not already exist.

        Safe to call on every module load — uses ``CREATE TABLE IF NOT EXISTS``.
        """
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    data       TEXT    NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_items(self, sort: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Return all items, optionally sorted by a JSON field.

        Args:
            sort: Optional dict with keys ``"field"`` (JSON field name inside
                  ``data``) and ``"order"`` (``"asc"`` or ``"desc"``).

        Returns:
            List of item dicts, each augmented with ``id``, ``created_at``,
            and ``updated_at`` from the row metadata.
        """
        query = "SELECT id, data, created_at, updated_at FROM items"
        if sort and "field" in sort:
            order = "DESC" if sort.get("order", "asc").lower() == "desc" else "ASC"
            query += f" ORDER BY json_extract(data, '$.{sort['field']}') {order}"

        conn = self._connect()
        try:
            rows = conn.execute(query).fetchall()
        finally:
            conn.close()

        return [_row_to_dict(row) for row in rows]

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single item by primary key.

        Returns:
            Item dict with metadata fields, or ``None`` if not found.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id, data, created_at, updated_at FROM items WHERE id = ?",
                (item_id,),
            ).fetchone()
        finally:
            conn.close()

        return _row_to_dict(row) if row else None

    def create_item(self, data: Dict[str, Any]) -> int:
        """Insert a new item and return its auto-assigned ID.

        Args:
            data: Arbitrary dict of app-specific fields.

        Returns:
            The new row's integer primary key.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO items (data) VALUES (?)",
                (json.dumps(data),),
            )
            item_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        return item_id

    def update_item(self, item_id: int, data: Dict[str, Any]) -> bool:
        """Replace the data blob for an existing item.

        Args:
            item_id: Primary key of the item to update.
            data:    New data dict (replaces existing blob entirely).

        Returns:
            ``True`` if the row was found and updated, ``False`` otherwise.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "UPDATE items SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(data), item_id),
            )
            affected = cursor.rowcount
            conn.commit()
        finally:
            conn.close()

        return affected > 0

    def delete_item(self, item_id: int) -> bool:
        """Delete an item by primary key.

        Returns:
            ``True`` if the row was found and deleted, ``False`` otherwise.
        """
        conn = self._connect()
        try:
            cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            affected = cursor.rowcount
            conn.commit()
        finally:
            conn.close()

        return affected > 0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Merge the JSON data blob with row-level metadata fields."""
    item: Dict[str, Any] = json.loads(row["data"])
    item["id"] = row["id"]
    item["created_at"] = row["created_at"]
    item["updated_at"] = row["updated_at"]
    return item
