"""Platform-wide SQLite database for AI features (embeddings, relationships, derived data).

Bounded context: Cross-app AI infrastructure.  Owns ``platform-ai.db`` and provides
typed access for embeddings, inter-item relationships, and derived metadata.
Intentionally separate from per-app databases so AI features can span apps without coupling.
All methods are synchronous; call from background threads if latency is a concern.
"""

from __future__ import annotations

import json
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
    """Manages platform-ai.db: embeddings, relationships, and derived data across all apps."""

    def __init__(self, db_path: Path = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Create tables and indexes (idempotent). Sets WAL mode once. Safe to call on startup."""
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
        """Insert or update an embedding; on conflict updates vector/model_version."""
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
        """Return embeddings (optionally filtered by app_name). Keys: app_name, item_id, vector, model_version."""
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
    # Relationships
    # ------------------------------------------------------------------

    def insert_relationship(
        self,
        from_app: str,
        from_item_id: int,
        to_app: str,
        to_item_id: int,
        relation_type: str,
        metadata: dict | None = None,
    ) -> None:
        """Insert a relationship edge, ignoring duplicates (UNIQUE constraint)."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO relationships"
                " (from_app, from_item_id, to_app, to_item_id, relation_type, metadata, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (from_app, from_item_id, to_app, to_item_id,
                 relation_type, json.dumps(metadata or {}), _utcnow()),
            )
        logger.debug(
            "ai_db: insert_relationship %s/%d -[%s]-> %s/%d",
            from_app, from_item_id, relation_type, to_app, to_item_id,
        )

    def delete_relationships_from(self, app_name: str, item_id: int) -> int:
        """Delete all edges where this item is the source. Returns count deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM relationships WHERE from_app = ? AND from_item_id = ?",
                (app_name, item_id),
            )
        count = cursor.rowcount
        if count:
            logger.debug("ai_db: deleted %d outgoing relationships from %s/%d", count, app_name, item_id)
        return count

    def get_relationships(self, app_name: str, item_id: int) -> list[dict]:
        """Return all edges where item is on from or to side. metadata is decoded from JSON.

        Uses UNION so SQLite can use idx_rel_from and idx_rel_to separately.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT from_app, from_item_id, to_app, to_item_id, relation_type, metadata"
                " FROM relationships WHERE from_app = ? AND from_item_id = ?"
                " UNION "
                "SELECT from_app, from_item_id, to_app, to_item_id, relation_type, metadata"
                " FROM relationships WHERE to_app = ? AND to_item_id = ?",
                (app_name, item_id, app_name, item_id),
            ).fetchall()
        return [
            {
                "from_app": r[0], "from_item_id": r[1],
                "to_app": r[2], "to_item_id": r[3],
                "relation_type": r[4], "metadata": json.loads(r[5] or "{}"),
            }
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL, item_id INTEGER NOT NULL,
    vector BLOB NOT NULL, model_version TEXT NOT NULL, created_at TIMESTAMP,
    UNIQUE(app_name, item_id)
);
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_app TEXT NOT NULL, from_item_id INTEGER NOT NULL,
    to_app TEXT NOT NULL, to_item_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL, metadata TEXT DEFAULT '{}', created_at TIMESTAMP,
    UNIQUE(from_app, from_item_id, to_app, to_item_id, relation_type)
);
CREATE TABLE IF NOT EXISTS derived_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL, derivation_type TEXT NOT NULL,
    data TEXT NOT NULL DEFAULT '{}', updated_at TIMESTAMP,
    UNIQUE(source_id, derivation_type)
);
CREATE INDEX IF NOT EXISTS idx_embeddings_app_item ON embeddings (app_name, item_id);
CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships (from_app, from_item_id);
CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships (to_app, to_item_id);
CREATE INDEX IF NOT EXISTS idx_derived_type ON derived_data (derivation_type);
"""

# Module-level singleton — initialized once at application startup via ai_db.init()
ai_db = AiDatabase()
