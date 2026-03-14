"""App discovery scanner for the shared-platform architecture.

Scans the apps/ directory and identifies valid app entries.  An app is
considered valid when its subdirectory contains **both**:

    apps/<name>/manifest.json  — app metadata (name, icon, description, …)
    apps/<name>/backend.py     — FastAPI router module

Invalid or partially-configured directories are logged as warnings and
skipped so that a broken app can never prevent the rest of the platform
from starting.

Typical usage
-------------
    from platform.discovery import discover_apps, AppEntry

    apps = discover_apps()          # list[AppEntry]
    for app in apps:
        print(app.name, app.path)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Root of the apps/ directory, relative to this file's location.
# Layout:  <project-root>/platform/discovery.py
#          <project-root>/apps/<appname>/
_APPS_DIR = Path(__file__).parent.parent / "apps"

# Files that must both be present for an app to be considered valid.
_REQUIRED_FILES = ("manifest.json", "backend.py")

# Required keys inside manifest.json.
_REQUIRED_MANIFEST_KEYS = ("name",)


@dataclass
class AppEntry:
    """Represents a fully-validated, discovered app.

    Attributes
    ----------
    app_id:
        Canonical identifier derived from the directory name (lowercase,
        no spaces).  Example: ``"todos"``, ``"razorblades"``.
    name:
        Human-readable display name from manifest.json.
    path:
        Absolute ``Path`` to the app's directory (``apps/<app_id>/``).
    manifest:
        Full contents of manifest.json as a plain dict.
    has_frontend:
        True when ``apps/<app_id>/frontend/dist/`` exists so the platform
        knows whether to serve static assets for this app.
    """

    app_id: str
    name: str
    path: Path
    manifest: dict = field(repr=False)
    has_frontend: bool = False

    @property
    def backend_module_path(self) -> Path:
        """Absolute path to this app's backend.py."""
        return self.path / "backend.py"

    @property
    def data_dir(self) -> Path:
        """Absolute path to this app's data directory (may not exist yet)."""
        return self.path / "data"

    @property
    def frontend_dist_dir(self) -> Path:
        """Absolute path to the built frontend assets (may not exist)."""
        return self.path / "frontend" / "dist"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_manifest(manifest_path: Path) -> Optional[dict]:
    """Parse and minimally validate a manifest.json file.

    Returns the parsed dict on success, or ``None`` if the file is
    malformed or missing required keys.
    """
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.warning("Skipping %s — invalid JSON: %s", manifest_path, exc)
        return None

    for key in _REQUIRED_MANIFEST_KEYS:
        if key not in data:
            logger.warning(
                "Skipping %s — manifest missing required key '%s'",
                manifest_path.parent.name,
                key,
            )
            return None

    return data


def _is_valid_app_dir(directory: Path) -> bool:
    """Return True when *directory* contains all required app files."""
    return all((directory / fname).is_file() for fname in _REQUIRED_FILES)


def _build_entry(app_dir: Path) -> Optional[AppEntry]:
    """Construct an :class:`AppEntry` from a candidate directory.

    Returns ``None`` if the directory does not meet validity requirements.
    """
    if not _is_valid_app_dir(app_dir):
        missing = [f for f in _REQUIRED_FILES if not (app_dir / f).is_file()]
        logger.debug(
            "Skipping '%s' — missing file(s): %s",
            app_dir.name,
            ", ".join(missing),
        )
        return None

    manifest = _load_manifest(app_dir / "manifest.json")
    if manifest is None:
        return None

    app_id = app_dir.name
    has_frontend = (app_dir / "frontend" / "dist").is_dir()

    return AppEntry(
        app_id=app_id,
        name=manifest["name"],
        path=app_dir,
        manifest=manifest,
        has_frontend=has_frontend,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover_apps(apps_dir: Optional[Path] = None) -> List[AppEntry]:
    """Scan *apps_dir* and return a list of valid :class:`AppEntry` objects.

    Parameters
    ----------
    apps_dir:
        Override the default apps/ directory path.  Mainly useful for
        testing.  Defaults to ``<project-root>/apps/``.

    Returns
    -------
    list[AppEntry]
        Sorted by ``app_id`` for deterministic ordering.  Directories that
        are missing required files, contain malformed manifests, or are not
        directories at all are silently skipped (with a DEBUG-level log).
    """
    root = apps_dir or _APPS_DIR

    if not root.is_dir():
        logger.error("Apps directory not found: %s", root)
        return []

    entries: List[AppEntry] = []

    for candidate in sorted(root.iterdir()):
        if not candidate.is_dir():
            # Skip loose files (e.g. old *.schema.json files).
            continue

        entry = _build_entry(candidate)
        if entry is not None:
            entries.append(entry)
            logger.info("Discovered app '%s' at %s", entry.app_id, entry.path)

    logger.info(
        "Discovery complete: %d valid app(s) found in %s", len(entries), root
    )
    return entries
