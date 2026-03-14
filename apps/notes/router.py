"""FastAPI router for the Notes app (read-only — notes are imported from the vault)."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.platform.app_db import AppDatabase

router = APIRouter()

_db = AppDatabase(Path(__file__).parent / "data" / "notes.db")
_db.init()

_DEFAULT_SORT = {"field": "title", "order": "asc"}


@router.get("/items", response_model=List[Dict[str, Any]])
def list_items(
    sort_field: Optional[str] = None,
    sort_order: str = "asc",
):
    sort = {"field": sort_field, "order": sort_order} if sort_field else _DEFAULT_SORT
    return _db.list_items(sort=sort)


@router.get("/items/{item_id}", response_model=Dict[str, Any])
def get_item(item_id: int):
    item = _db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item
