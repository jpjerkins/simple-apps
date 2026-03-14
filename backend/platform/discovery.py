"""App discovery scanner.

Scans the ``apps/`` directory for sub-directories that contain a
``manifest.json``.  Each valid manifest is parsed, its router module is
dynamically imported, and an :class:`AppManifest` dataclass is returned.

Usage (from the platform entrypoint)::

    from backend.platform.discovery import discover_apps

    for manifest in discover_apps():
        app.include_router(manifest.router, prefix=manifest.api_prefix)

Adding a New App
----------------
1. Create ``apps/<name>/`` with a ``manifest.json`` (see
   ``apps/_template/manifest.json`` for the required shape).
2. Add ``apps/<name>/router.py`` that defines a module-level ``router``
   variable of type ``fastapi.APIRouter``.
3. Restart the container — no changes to platform code are needed.

Discovery Rules
---------------
- Only immediate sub-directories of ``apps/`` are scanned (not recursive).
- Directories beginning with ``_`` (e.g. ``_template``) are skipped.
- Directories without a ``manifest.json`` are silently skipped.
- Apps whose router module fails to import are skipped with an ERROR log;
  the platform continues loading the remaining apps.
"""

from __future__ import annotations

import importlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)

_APPS_DIR = Path(__file__).parent.parent.parent / "apps"

_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "name",
    "label",
    "version",
    "description",
    "url_prefix",
    "db_path",
    "router_module",
    "frontend_dist",
})


@dataclass
class AppManifest:
    """Parsed and validated representation of a single app's ``manifest.json``.

    Attributes:
        name:            Machine-readable slug (e.g. ``"todos"``).
        label:           Human-readable display name (e.g. ``"To-Do List"``).
        version:         Semantic version string (e.g. ``"1.0.0"``).
        description:     One-sentence description of the app.
        url_prefix:      URL path where the frontend is served (e.g. ``"/todos"``).
        api_prefix:      URL path prefix for API routes (e.g. ``"/api/todos"``).
        db_path:         Absolute path to the app's SQLite database file.
        router_module:   Dotted Python module path containing the ``router`` var.
        frontend_dist:   Absolute path to the compiled Vite ``dist/`` folder.
        icon:            Emoji or short string icon (optional).
        events_emits:    Event types this app will publish (future use).
        events_consumes: Event types this app subscribes to (future use).
        metadata:        Arbitrary extra config from the manifest (pass-through).
        router:          The loaded ``APIRouter`` instance (populated by scanner).
    """

    name: str
    label: str
    version: str
    description: str
    url_prefix: str
    api_prefix: str
    db_path: Path
    router_module: str
    frontend_dist: Path
    icon: str = ""
    events_emits: List[str] = field(default_factory=list)
    events_consumes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    router: Optional[APIRouter] = None


def discover_apps(apps_dir: Path = _APPS_DIR) -> List[AppManifest]:
    """Scan *apps_dir* and return a loaded :class:`AppManifest` for each valid app.

    Args:
        apps_dir: Directory to scan.  Defaults to the repository ``apps/`` folder.

    Returns:
        Alphabetically sorted list of :class:`AppManifest` objects with
        ``.router`` populated.  Apps that fail to load are skipped; errors are
        written to the ``backend.platform.discovery`` logger.
    """
    loaded: List[AppManifest] = []

    if not apps_dir.exists():
        logger.warning("Apps directory not found: %s", apps_dir)
        return loaded

    for app_dir in sorted(apps_dir.iterdir()):
        if not app_dir.is_dir() or app_dir.name.startswith("_"):
            continue

        manifest_file = app_dir / "manifest.json"
        if not manifest_file.exists():
            continue

        try:
            manifest = _load_manifest(manifest_file, apps_dir.parent)
            loaded.append(manifest)
            logger.info(
                "Discovered app: %s  (%s)  api=%s",
                manifest.name,
                manifest.label,
                manifest.api_prefix,
            )
        except Exception:
            logger.exception("Failed to load app at %s — skipping", app_dir)

    if not loaded:
        logger.warning("No apps discovered in %s", apps_dir)
    else:
        logger.info("Total apps loaded: %d", len(loaded))

    return loaded


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_manifest(manifest_file: Path, repo_root: Path) -> AppManifest:
    """Parse *manifest_file*, validate required fields, import the router."""
    with manifest_file.open(encoding="utf-8") as fh:
        raw: Dict[str, Any] = json.load(fh)

    _validate_manifest(raw, manifest_file)

    events = raw.get("events", {})
    manifest = AppManifest(
        name=raw["name"],
        label=raw["label"],
        version=raw["version"],
        description=raw["description"],
        url_prefix=raw["url_prefix"],
        api_prefix=raw.get("api_prefix", f"/api/{raw['name']}"),
        db_path=repo_root / raw["db_path"],
        router_module=raw["router_module"],
        frontend_dist=repo_root / raw["frontend_dist"],
        icon=raw.get("icon", ""),
        events_emits=events.get("emits", []),
        events_consumes=events.get("consumes", []),
        metadata=raw.get("metadata", {}),
    )

    manifest.router = _import_router(manifest.router_module)
    return manifest


def _validate_manifest(raw: Dict[str, Any], manifest_file: Path) -> None:
    """Raise ``ValueError`` if any required manifest fields are absent."""
    missing = _REQUIRED_FIELDS - raw.keys()
    if missing:
        raise ValueError(
            f"{manifest_file}: missing required field(s): {sorted(missing)}"
        )


def _import_router(module_path: str) -> APIRouter:
    """Import *module_path* and return its ``router`` attribute.

    Args:
        module_path: Dotted Python module path, e.g. ``"apps.todos.router"``.

    Returns:
        The ``APIRouter`` instance found in the module.

    Raises:
        ImportError:    Module cannot be imported.
        AttributeError: Module has no ``router`` attribute.
        TypeError:      ``router`` is not an ``APIRouter`` instance.
    """
    module = importlib.import_module(module_path)

    if not hasattr(module, "router"):
        raise AttributeError(
            f"Module '{module_path}' must define a module-level 'router' variable "
            f"of type fastapi.APIRouter"
        )

    router = module.router
    if not isinstance(router, APIRouter):
        raise TypeError(
            f"Module '{module_path}': 'router' must be an APIRouter instance, "
            f"got {type(router)!r}"
        )

    return router
