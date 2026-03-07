"""Generic CRUD operations for all apps."""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from . import db


def list_items(app_id: str, filters: Optional[Dict] = None, sort: Optional[Dict] = None) -> List[Dict]:
    """List all items for an app with optional filtering and sorting."""
    conn = db.get_connection()
    cursor = conn.cursor()

    query = "SELECT id, data, created_at, updated_at FROM app_items WHERE app_id = ?"
    params = [app_id]

    if sort and "field" in sort:
        order = sort.get("order", "asc").upper()
        query += f" ORDER BY json_extract(data, '$.{sort['field']}') {order}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        item = json.loads(row["data"])
        item["id"] = row["id"]
        item["created_at"] = row["created_at"]
        item["updated_at"] = row["updated_at"]
        items.append(item)

    return items


def get_item(app_id: str, item_id: int) -> Optional[Dict]:
    """Get a single item by ID."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, data, created_at, updated_at FROM app_items WHERE app_id = ? AND id = ?",
        (app_id, item_id)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    item = json.loads(row["data"])
    item["id"] = row["id"]
    item["created_at"] = row["created_at"]
    item["updated_at"] = row["updated_at"]
    return item


def create_item(app_id: str, data: Dict[str, Any]) -> int:
    """Create a new item."""
    conn = db.get_connection()
    cursor = conn.cursor()

    data_json = json.dumps(data)
    cursor.execute(
        "INSERT INTO app_items (app_id, data) VALUES (?, ?)",
        (app_id, data_json)
    )

    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id


def update_item(app_id: str, item_id: int, data: Dict[str, Any]) -> bool:
    """Update an existing item."""
    conn = db.get_connection()
    cursor = conn.cursor()

    data_json = json.dumps(data)
    cursor.execute(
        "UPDATE app_items SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE app_id = ? AND id = ?",
        (data_json, app_id, item_id)
    )

    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_item(app_id: str, item_id: int) -> bool:
    """Delete an item."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM app_items WHERE app_id = ? AND id = ?",
        (app_id, item_id)
    )

    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0
