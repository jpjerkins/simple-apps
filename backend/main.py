"""FastAPI application — shared platform entrypoint.

Discovers all apps under apps/*/manifest.json at startup, mounts each app's
APIRouter at its declared api_prefix, and serves each app's compiled frontend
at its url_prefix.

Adding a new app never requires changes here — drop a manifest.json and a
router.py into apps/<name>/ and restart the container.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.event_bus import subscribe
from backend.handlers.embedding_handler import (
    handle_item_created,
    handle_item_deleted,
    handle_item_updated,
)
from backend.handlers.relationship_handler import (
    handle_item_created as rel_handle_created,
    handle_item_updated as rel_handle_updated,
)
from backend.platform.ai_db import ai_db
from backend.platform.discovery import discover_apps
from backend.platform.relationship_queries import get_related
from backend.platform.semantic_search import search as semantic_search
from backend.services.file_watcher import start_file_watcher


class SemanticSearchRequest(BaseModel):
    query: str
    app_name: str | None = None
    limit: int = 10


_PLATFORM_STATIC = Path(__file__).parent.parent / "platform" / "static"

app = FastAPI(title="Simple Apps Platform")

# ---------------------------------------------------------------------------
# App discovery — runs at import time, before the first request
# ---------------------------------------------------------------------------

_manifests = discover_apps()

# ---------------------------------------------------------------------------
# AI platform startup — initialize DB and wire embedding handlers
# ---------------------------------------------------------------------------

ai_db.init()
start_file_watcher()
for _m in _manifests:
    subscribe(f"{_m.name}.item.created", handle_item_created)
    subscribe(f"{_m.name}.item.updated", handle_item_updated)
    subscribe(f"{_m.name}.item.deleted", handle_item_deleted)
    subscribe(f"{_m.name}.item.created", rel_handle_created)
    subscribe(f"{_m.name}.item.updated", rel_handle_updated)

# ---------------------------------------------------------------------------
# Mount app routers and frontends
# ---------------------------------------------------------------------------

for _m in _manifests:
    app.include_router(_m.router, prefix=_m.api_prefix, tags=[_m.label])
    if _m.frontend_dist.is_dir():
        app.mount(
            _m.url_prefix,
            StaticFiles(directory=_m.frontend_dist, html=True),
            name=_m.name,
        )


# ---------------------------------------------------------------------------
# Platform-level routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """Serve the platform home page."""
    return FileResponse(_PLATFORM_STATIC / "index.html")


@app.get("/api/apps")
def list_apps() -> JSONResponse:
    """Return metadata for all discovered apps — used by the home page."""
    return JSONResponse([
        {
            "name": m.name,
            "label": m.label,
            "version": m.version,
            "description": m.description,
            "icon": m.icon,
            "url_prefix": m.url_prefix,
        }
        for m in _manifests
    ])


@app.post("/api/search/semantic")
def semantic_search_route(request: SemanticSearchRequest) -> JSONResponse:
    """Return items semantically similar to the query, ranked by cosine similarity."""
    return JSONResponse(semantic_search(request.query, request.app_name, request.limit))


@app.get("/api/relationships/{app_name}/{item_id}")
def get_relationships_route(
    app_name: str,
    item_id: int,
    relation_type: str | None = None,
    max_depth: int = 2,
) -> JSONResponse:
    """Return items related to the given item via BFS graph traversal.

    Query params:
        relation_type: Filter to a specific edge type (e.g. ``recommended_by``).
        max_depth:     Number of hops to follow (1–3; capped at 3).
    """
    results = get_related(item_id, app_name, relation_type, max_depth)
    return JSONResponse(results)
