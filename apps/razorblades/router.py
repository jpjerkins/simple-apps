"""FastAPI router for the Razor Blade Tracker app."""

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.platform.app_db import AppDatabase
from backend.event_bus import publish

router = APIRouter()

_db = AppDatabase(Path(__file__).parent / "data" / "razorblades.db")
_db.init()

_DEFAULT_SORT = {"field": "startDate", "order": "desc"}


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
    # Ensure usages array is always present
    item.setdefault("usages", [])
    item_id = _db.create_item(item)
    created = _db.get_item(item_id)
    publish("razorblades.blade.created", {"id": item_id, **item})
    return created


@router.get("/items/{item_id}", response_model=Dict[str, Any])
def get_item(item_id: int):
    item = _db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@router.put("/items/{item_id}", response_model=Dict[str, Any])
def update_item(item_id: int, item: Dict[str, Any]):
    item.setdefault("usages", [])
    if not _db.update_item(item_id, item):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    updated = _db.get_item(item_id)
    # Publish specialised event when a blade is retired
    if item.get("status") == "retired":
        publish("razorblades.blade.retired", {"id": item_id, **item})
    return updated


@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    if not _db.delete_item(item_id):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return {"success": True}


# ---------------------------------------------------------------------------
# Quick-action routes
# ---------------------------------------------------------------------------

@router.post("/actions/use", response_model=Dict[str, Any])
def use_razor():
    """Append today's date to the newest active blade's usages."""
    today = datetime.date.today().isoformat()
    items = _db.list_items(sort=_DEFAULT_SORT)
    active = [i for i in items if i.get("status") == "active"]
    if not active:
        raise HTTPException(status_code=404, detail="No active razor blade found")
    blade = active[0]
    blade_id = blade.pop("id")
    blade.pop("created_at", None)
    blade.pop("updated_at", None)
    blade.setdefault("usages", []).append(today)
    _db.update_item(blade_id, blade)
    updated = _db.get_item(blade_id)
    publish("razorblades.blade.updated", {"id": blade_id, **blade})
    return updated


@router.post("/actions/new-razor", response_model=Dict[str, Any])
def new_razor():
    """Retire all active blades and create a fresh one with today as first use."""
    today = datetime.date.today().isoformat()
    items = _db.list_items()
    for blade in items:
        if blade.get("status") == "active":
            blade_id = blade.pop("id")
            blade.pop("created_at", None)
            blade.pop("updated_at", None)
            blade["status"] = "retired"
            _db.update_item(blade_id, blade)
            publish("razorblades.blade.retired", {"id": blade_id, **blade})
    new_id = _db.create_item({
        "brand": "Feather",
        "startDate": today,
        "usages": [today],
        "status": "active",
    })
    created = _db.get_item(new_id)
    publish("razorblades.blade.created", {"id": new_id, **created})
    return created
