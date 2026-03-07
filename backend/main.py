"""FastAPI application with generic CRUD API."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path

from . import db, crud, schema_registry

app = FastAPI(title="Simple Apps Platform")

# Initialize database on startup
db.init_db()

# Pydantic models for request/response
class ItemData(BaseModel):
    data: Dict[str, Any]


@app.get("/api/schemas")
def get_schemas():
    """Return all app schemas."""
    return schema_registry.get_all()


@app.get("/api/{app_id}/items")
def list_items(app_id: str, sort_field: Optional[str] = None, sort_order: Optional[str] = "asc"):
    """List all items for an app."""
    schema = schema_registry.get(app_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")

    sort = None
    if sort_field:
        sort = {"field": sort_field, "order": sort_order}
    elif "defaultSort" in schema:
        sort = schema["defaultSort"]

    return crud.list_items(app_id, sort=sort)


@app.get("/api/{app_id}/items/{item_id}")
def get_item(app_id: str, item_id: int):
    """Get a single item."""
    schema = schema_registry.get(app_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")

    item = crud.get_item(app_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    return item


@app.post("/api/{app_id}/items")
def create_item(app_id: str, item: Dict[str, Any]):
    """Create a new item."""
    schema = schema_registry.get(app_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")

    item_id = crud.create_item(app_id, item)
    return {"id": item_id, **item}


@app.put("/api/{app_id}/items/{item_id}")
def update_item(app_id: str, item_id: int, item: Dict[str, Any]):
    """Update an existing item."""
    schema = schema_registry.get(app_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")

    success = crud.update_item(app_id, item_id, item)
    if not success:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    return {"id": item_id, **item}


@app.delete("/api/{app_id}/items/{item_id}")
def delete_item(app_id: str, item_id: int):
    """Delete an item."""
    schema = schema_registry.get(app_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")

    success = crud.delete_item(app_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    return {"success": True}


# Serve static files (frontend)
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_dir.exists():
    # Mount static assets (JS, CSS, etc.)
    app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

    # Catch-all route for SPA - serve index.html for any non-API path
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for SPA routing (catch-all for non-API routes)."""
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not found")
