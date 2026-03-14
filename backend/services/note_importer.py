"""Import Obsidian markdown notes into the notes AppDatabase.

Parses YAML frontmatter and markdown content, upserts into notes.db,
generates embeddings, and stores ![[simple-apps/app_name/item_id]] relationships.

Vault path is controlled by the NOTES_VAULT_PATH environment variable
(default: /app/notes in the container).
"""

from __future__ import annotations

import logging
import os
import re
import threading
from pathlib import Path
from typing import Optional

import yaml

from backend.handlers.embedding_handler import _generate_and_store
from backend.platform.ai_db import ai_db
from backend.platform.app_db import AppDatabase

logger = logging.getLogger(__name__)

_APP_NAME = "notes"
VAULT_PATH = Path(os.environ.get("NOTES_VAULT_PATH", "/app/notes"))
_DB_PATH = Path(__file__).parent.parent.parent / "apps" / "notes" / "data" / "notes.db"

# Matches ![[simple-apps/app_name/item_id]] in note content
_LINK_RE = re.compile(r"!\[\[simple-apps/(\w+)/(\d+)\]\]")

# Cap stored content to avoid very large JSON blobs
_CONTENT_MAX_CHARS = 4000

_db = AppDatabase(_DB_PATH)
_db.init()

# path (relative to vault) → item_id — populated lazily on first import
_path_map: dict[str, int] = {}
_path_map_lock = threading.Lock()
_initialized = False


def _ensure_path_map() -> None:
    """Populate _path_map from the DB on first call (thread-safe, idempotent)."""
    global _initialized
    if _initialized:
        return
    with _path_map_lock:
        if _initialized:
            return
        for item in _db.list_items():
            path = item.get("path")
            if path:
                _path_map[path] = item["id"]
        _initialized = True


def _parse_note(file_path: Path) -> Optional[dict]:
    """Parse a markdown file into a data dict. Returns None on read/parse error."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        logger.exception("note_importer: cannot read %s", file_path)
        return None

    frontmatter: dict = {}
    content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                logger.warning("note_importer: invalid frontmatter in %s", file_path)
            content = parts[2].lstrip("\n")

    title = frontmatter.get("title") or file_path.stem
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    extra = {k: str(v) for k, v in frontmatter.items() if k not in ("title", "tags")}

    return {
        "path": str(file_path.relative_to(VAULT_PATH)),
        "title": title,
        "tags": tags,
        "content": content[:_CONTENT_MAX_CHARS],
        "frontmatter": extra,
    }


def _store_relationships(item_id: int, content: str) -> None:
    """Replace outgoing 'references' relationships for this note with current links."""
    ai_db.delete_relationships_from(_APP_NAME, item_id)
    for m in _LINK_RE.finditer(content):
        linked_app = m.group(1)
        linked_item_id = int(m.group(2))
        ai_db.insert_relationship(
            from_app=_APP_NAME,
            from_item_id=item_id,
            to_app=linked_app,
            to_item_id=linked_item_id,
            relation_type="references",
        )


def import_note(file_path: Path) -> None:
    """Upsert a note from *file_path* into notes.db and refresh its embedding."""
    _ensure_path_map()

    data = _parse_note(file_path)
    if data is None:
        return

    rel_path = data["path"]
    existing_id = _path_map.get(rel_path)

    try:
        if existing_id is not None:
            _db.update_item(existing_id, data)
            item_id = existing_id
        else:
            item_id = _db.create_item(data)
            with _path_map_lock:
                _path_map[rel_path] = item_id

        _generate_and_store(_APP_NAME, item_id, data)
        _store_relationships(item_id, data.get("content", ""))
        logger.info("note_importer: upserted %r (id=%d)", rel_path, item_id)

    except Exception:
        logger.exception("note_importer: failed to import %s", file_path)
