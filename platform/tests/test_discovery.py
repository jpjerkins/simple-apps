"""Tests for platform.discovery — app auto-discovery scanner."""

import json
import pytest
from pathlib import Path

from platform.discovery import discover_apps, AppEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_app(tmp_path: Path, name: str, manifest: dict, *, with_backend: bool = True) -> Path:
    """Helper: create a minimal app directory under tmp_path."""
    app_dir = tmp_path / name
    app_dir.mkdir()

    (app_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    if with_backend:
        (app_dir / "backend.py").write_text(
            "# placeholder backend\nrouter = None\n", encoding="utf-8"
        )

    return app_dir


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_discover_single_valid_app(tmp_path):
    """A directory with manifest.json + backend.py is discovered."""
    _make_app(tmp_path, "todos", {"name": "To-Do List"})

    apps = discover_apps(tmp_path)

    assert len(apps) == 1
    app = apps[0]
    assert isinstance(app, AppEntry)
    assert app.app_id == "todos"
    assert app.name == "To-Do List"
    assert app.path == tmp_path / "todos"


def test_discover_multiple_apps_sorted(tmp_path):
    """Multiple valid apps are returned in alphabetical order."""
    _make_app(tmp_path, "zebra", {"name": "Zebra App"})
    _make_app(tmp_path, "alpha", {"name": "Alpha App"})
    _make_app(tmp_path, "middle", {"name": "Middle App"})

    apps = discover_apps(tmp_path)

    assert [a.app_id for a in apps] == ["alpha", "middle", "zebra"]


def test_manifest_extra_fields_preserved(tmp_path):
    """Extra fields in manifest.json are available via AppEntry.manifest."""
    manifest = {
        "name": "Books",
        "icon": "📚",
        "description": "Reading list",
        "version": "1.0.0",
    }
    _make_app(tmp_path, "books", manifest)

    apps = discover_apps(tmp_path)

    assert apps[0].manifest["icon"] == "📚"
    assert apps[0].manifest["description"] == "Reading list"


def test_has_frontend_false_when_dist_missing(tmp_path):
    """has_frontend is False when frontend/dist/ does not exist."""
    _make_app(tmp_path, "todos", {"name": "Todos"})

    apps = discover_apps(tmp_path)

    assert apps[0].has_frontend is False


def test_has_frontend_true_when_dist_exists(tmp_path):
    """has_frontend is True when frontend/dist/ directory exists."""
    app_dir = _make_app(tmp_path, "todos", {"name": "Todos"})
    (app_dir / "frontend" / "dist").mkdir(parents=True)

    apps = discover_apps(tmp_path)

    assert apps[0].has_frontend is True


def test_derived_paths(tmp_path):
    """backend_module_path, data_dir, and frontend_dist_dir are correct."""
    app_dir = _make_app(tmp_path, "todos", {"name": "Todos"})

    apps = discover_apps(tmp_path)
    entry = apps[0]

    assert entry.backend_module_path == app_dir / "backend.py"
    assert entry.data_dir == app_dir / "data"
    assert entry.frontend_dist_dir == app_dir / "frontend" / "dist"


# ---------------------------------------------------------------------------
# Skipping / error cases
# ---------------------------------------------------------------------------

def test_skip_dir_missing_backend(tmp_path):
    """Directory with only manifest.json (no backend.py) is skipped."""
    _make_app(tmp_path, "no-backend", {"name": "No Backend"}, with_backend=False)

    apps = discover_apps(tmp_path)

    assert apps == []


def test_skip_dir_missing_manifest(tmp_path):
    """Directory with only backend.py (no manifest.json) is skipped."""
    app_dir = tmp_path / "no-manifest"
    app_dir.mkdir()
    (app_dir / "backend.py").write_text("router = None\n")

    apps = discover_apps(tmp_path)

    assert apps == []


def test_skip_loose_files_in_apps_dir(tmp_path):
    """Loose files (e.g. old *.schema.json) in apps/ root are ignored."""
    (tmp_path / "old.schema.json").write_text("{}")
    (tmp_path / "README.md").write_text("# readme")
    _make_app(tmp_path, "valid-app", {"name": "Valid"})

    apps = discover_apps(tmp_path)

    assert len(apps) == 1
    assert apps[0].app_id == "valid-app"


def test_skip_invalid_json_manifest(tmp_path):
    """A directory with malformed manifest.json is skipped."""
    app_dir = tmp_path / "broken"
    app_dir.mkdir()
    (app_dir / "manifest.json").write_text("{not valid json", encoding="utf-8")
    (app_dir / "backend.py").write_text("router = None\n")

    apps = discover_apps(tmp_path)

    assert apps == []


def test_skip_manifest_missing_name_key(tmp_path):
    """A manifest without the required 'name' key is skipped."""
    _make_app(tmp_path, "nameless", {"icon": "❓"})

    apps = discover_apps(tmp_path)

    assert apps == []


def test_empty_apps_dir_returns_empty_list(tmp_path):
    """An empty apps/ directory returns an empty list without errors."""
    apps = discover_apps(tmp_path)

    assert apps == []


def test_nonexistent_apps_dir_returns_empty_list(tmp_path):
    """A non-existent apps/ path returns an empty list without raising."""
    apps = discover_apps(tmp_path / "does_not_exist")

    assert apps == []


def test_mixed_valid_and_invalid_apps(tmp_path):
    """Only fully-valid apps are returned; broken ones are silently skipped."""
    _make_app(tmp_path, "good-one", {"name": "Good"})
    _make_app(tmp_path, "good-two", {"name": "Also Good"})
    _make_app(tmp_path, "no-backend", {"name": "No Backend"}, with_backend=False)

    broken = tmp_path / "bad-json"
    broken.mkdir()
    (broken / "manifest.json").write_text("{broken", encoding="utf-8")
    (broken / "backend.py").write_text("router = None\n")

    apps = discover_apps(tmp_path)

    assert {a.app_id for a in apps} == {"good-one", "good-two"}
