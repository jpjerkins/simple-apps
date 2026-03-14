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

from backend.platform.discovery import discover_apps

_PLATFORM_STATIC = Path(__file__).parent.parent / "platform" / "static"

app = FastAPI(title="Simple Apps Platform")

# ---------------------------------------------------------------------------
# App discovery — runs at import time, before the first request
# ---------------------------------------------------------------------------

_manifests = discover_apps()

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
