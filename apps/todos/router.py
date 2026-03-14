"""FastAPI router for the To-Do List app."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.platform.app_db import AppDatabase
from backend.event_bus import publish

router = APIRouter()

_db = AppDatabase(Path(__file__).parent / "data" / "todos.db")
_db.init()

_DEFAULT_SORT = {"field": "dueDate", "order": "asc"}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/items", response_model=List[Dict[str, Any]])
def list_items(
    sort_field: Optional[str] = None,
    sort_order: str = "asc",
):
    sort = {"field": sort_field, "order": sort_order} if sort_field else _DEFAULT_SORT
    return _db.list_items(sort=sort)


@router.post("/items", response_model=Dict[str, Any], status_code=201)
def create_item(item: Dict[str, Any]):
    item_id = _db.create_item(item)
    created = _db.get_item(item_id)
    publish("todos.item.created", {"id": item_id, **item})
    return created


@router.get("/items/{item_id}", response_model=Dict[str, Any])
def get_item(item_id: int):
    item = _db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@router.put("/items/{item_id}", response_model=Dict[str, Any])
def update_item(item_id: int, item: Dict[str, Any]):
    if not _db.update_item(item_id, item):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    updated = _db.get_item(item_id)
    publish("todos.item.updated", {"id": item_id, **item})
    return updated


@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    if not _db.delete_item(item_id):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    publish("todos.item.deleted", {"id": item_id})
    return {"success": True}
