"""Platform-wide SQLite database for AI features (embeddings, relationships, derived data).

Bounded context: Cross-app AI infrastructure.

This module owns the ``platform-ai.db`` SQLite file and provides typed
access methods for storing and retrieving ML-generated data (embeddings,
inter-item relationships, derived metadata). It is intentionally separate
from per-app databases so AI features can span multiple apps without coupling.

All methods are synchronous — callers should run them from background threads
if latency is a concern (the event bus already does this for handlers).
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = (
    Path(__file__).parent.parent.parent / "apps" / "platform" / "data" / "platform-ai.db"
)


class AiDatabase:
    """Manages the platform-wide AI SQLite database.

    Stores embeddings, inter-item relationships, and other derived data
    that cuts across individual app databases.

    Usage::

        ai_db.init()  # idempotent — safe to call on every startup
        ai_db.upsert_embedding("books", 42, vector_bytes, "all-MiniLM-L6-v2")
    """

    def __init__(self, db_path: Path = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Create tables and indexes if they do not exist (idempotent).

        Sets WAL mode once (a persistent DB-level setting) and creates
        all tables. Safe to call on every startup.
        """
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA_SQL)
        logger.info("ai_db: initialized at %s", self._db_path)

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def upsert_embedding(
        self,
        app_name: str,
        item_id: int,
        vector: bytes,
        model_version: str,
    ) -> None:
        """Insert or update the embedding for a single item.

        On conflict, updates vector and model_version but preserves created_at.
        """
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO embeddings (app_name, item_id, vector, model_version, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(app_name, item_id) DO UPDATE SET
                    vector=excluded.vector,
                    model_version=excluded.model_version
                """,
                (app_name, item_id, vector, model_version, now),
            )
        logger.debug("ai_db: upserted embedding app=%s item_id=%d", app_name, item_id)

    def delete_embedding(self, app_name: str, item_id: int) -> bool:
        """Remove an embedding. Returns True if a row was deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM embeddings WHERE app_name = ? AND item_id = ?",
                (app_name, item_id),
            )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug("ai_db: deleted embedding app=%s item_id=%d", app_name, item_id)
        return deleted

    def list_embeddings(self, app_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return embeddings, optionally filtered by app_name.

        Returns:
            List of dicts with keys: app_name, item_id, vector, model_version.
        """
        with self._connect() as conn:
            if app_name is not None:
                rows = conn.execute(
                    "SELECT app_name, item_id, vector, model_version FROM embeddings"
                    " WHERE app_name = ?",
                    (app_name,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT app_name, item_id, vector, model_version FROM embeddings"
                ).fetchall()
        return [
            {"app_name": r[0], "item_id": r[1], "vector": r[2], "model_version": r[3]}
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection. WAL is set once in init(); foreign_keys per-connection."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def _utcnow() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS embeddings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name      TEXT NOT NULL,
    item_id       INTEGER NOT NULL,
    vector        BLOB NOT NULL,
    model_version TEXT NOT NULL,
    created_at    TIMESTAMP,
    UNIQUE(app_name, item_id)
);

CREATE TABLE IF NOT EXISTS relationships (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    from_app      TEXT NOT NULL,
    from_item_id  INTEGER NOT NULL,
    to_app        TEXT NOT NULL,
    to_item_id    INTEGER NOT NULL,
    relation_type TEXT NOT NULL,
    metadata      TEXT DEFAULT '{}',
    created_at    TIMESTAMP,
    UNIQUE(from_app, from_item_id, to_app, to_item_id, relation_type)
);

CREATE TABLE IF NOT EXISTS derived_data (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id        TEXT NOT NULL,
    derivation_type  TEXT NOT NULL,
    data             TEXT NOT NULL DEFAULT '{}',
    updated_at       TIMESTAMP,
    UNIQUE(source_id, derivation_type)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_app_item
    ON embeddings (app_name, item_id);

CREATE INDEX IF NOT EXISTS idx_rel_from
    ON relationships (from_app, from_item_id);

CREATE INDEX IF NOT EXISTS idx_rel_to
    ON relationships (to_app, to_item_id);

CREATE INDEX IF NOT EXISTS idx_derived_type
    ON derived_data (derivation_type);
"""

# Module-level singleton — initialized once at application startup via ai_db.init()
ai_db = AiDatabase()
