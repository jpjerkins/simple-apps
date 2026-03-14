"""Extract and store relationships for all existing items.

Run inside the container:
    docker exec <container> python scripts/backfill_relationships.py

Scans apps/*/manifest.json directly (avoids importing discovery.py which
pulls in FastAPI). Uses INSERT OR IGNORE — safe to re-run. Existing
relationships are not duplicated.
"""

import json
import sqlite3
import sys
from pathlib import Path

# Container working directory is /app; backend package lives there.
sys.path.insert(0, "/app")

from backend.platform.ai_db import AiDatabase  # noqa: E402
from backend.platform.app_db import AppDatabase  # noqa: E402
from backend.handlers.relationship_handler import _EXTRACTORS  # noqa: E402

_PROJECT_ROOT = Path("/app")
_APPS_DIR = _PROJECT_ROOT / "apps"


def _discover_apps() -> list[dict]:
    """Return list of {name, db_path} dicts by scanning apps/*/manifest.json."""
    apps = []
    for manifest_path in sorted(_APPS_DIR.glob("*/manifest.json")):
        with manifest_path.open() as f:
            manifest = json.load(f)
        raw_db_path = manifest.get("db_path")
        if not raw_db_path:
            continue
        apps.append({
            "name": manifest["name"],
            "db_path": _PROJECT_ROOT / raw_db_path,
        })
    return apps


def _count_relationships(ai_db: AiDatabase) -> int:
    """Return current total row count in the relationships table."""
    with ai_db._connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]


def main() -> None:
    ai_db = AiDatabase()
    ai_db.init()

    total_before = _count_relationships(ai_db)
    total_inserted = 0

    for app in _discover_apps():
        app_name = app["name"]
        db_path = app["db_path"]
        extractor = _EXTRACTORS.get(app_name)

        if extractor is None:
            print(f"{app_name}: no relationship extractor registered, skipping")
            continue

        if not db_path.exists():
            print(f"{app_name}: db not found at {db_path}, skipping")
            continue

        app_db = AppDatabase(db_path)
        items = app_db.list_items()
        before = _count_relationships(ai_db)

        for item in items:
            extractor(item["id"], item)

        after = _count_relationships(ai_db)
        inserted = after - before
        total_inserted += inserted
        print(f"{app_name}: processed {len(items)} items, {inserted} relationships inserted")

    total_after = _count_relationships(ai_db)
    print(f"\nDone. Relationships before: {total_before}, after: {total_after}, net new: {total_inserted}")


if __name__ == "__main__":
    main()
