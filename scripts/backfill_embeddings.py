"""Generate embeddings for all existing items that don't have one yet.

Run inside the container:
    docker exec <container> python scripts/backfill_embeddings.py

Scans apps/*/manifest.json directly (avoids importing discovery.py which
pulls in FastAPI). Skips items that already have an embedding. Safe to re-run.
"""

# Pre-cache stdlib `platform` before sys.path is modified.
# The top-level platform/ package in this repo would shadow the stdlib module
# once /app is prepended to sys.path, breaking torch (which calls platform.system()).
import platform as _stdlib_platform  # noqa: F401 — keep in sys.modules

import json
import sys
from pathlib import Path

# Container working directory is /app; backend package lives there.
sys.path.insert(0, "/app")

from backend.platform.ai_db import AiDatabase  # noqa: E402
from backend.platform.app_db import AppDatabase  # noqa: E402
from backend.handlers.embedding_handler import (  # noqa: E402
    _MODEL_NAME,
    _encode_vector,
    _get_model,
    create_embedding_text,
)

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


def main() -> None:
    ai_db = AiDatabase()
    ai_db.init()

    print("Loading embedding model...")
    model = _get_model()
    print(f"Model ready: {_MODEL_NAME}")

    total_embedded = 0

    for app in _discover_apps():
        app_name = app["name"]
        db_path = app["db_path"]

        if not db_path.exists():
            print(f"{app_name}: db not found at {db_path}, skipping")
            continue

        app_db = AppDatabase(db_path)
        items = app_db.list_items()

        existing_ids = {
            row["item_id"]
            for row in ai_db.list_embeddings(app_name)
        }

        missing = [item for item in items if item["id"] not in existing_ids]
        print(f"{app_name}: {len(existing_ids)} existing, {len(missing)} to embed")

        for n, item in enumerate(missing, start=1):
            item_id = item["id"]
            text = create_embedding_text(app_name, item)
            raw_vector = model.encode(text)
            vector_bytes = _encode_vector(raw_vector)
            ai_db.upsert_embedding(app_name, item_id, vector_bytes, _MODEL_NAME)
            print(f"  {app_name}: {n}/{len(missing)} embedded (id={item_id})")
            total_embedded += 1

    print(f"\nDone. Total embeddings created: {total_embedded}")


if __name__ == "__main__":
    main()
