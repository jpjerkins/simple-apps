"""Semantic search over all app items using vector embeddings.

Computes cosine similarity between a query embedding and all stored item
embeddings, then fetches full item data from each app's SQLite database.
The SentenceTransformer singleton is reused from embedding_handler.
App databases are lazily discovered via discover_apps() and cached for
the lifetime of the process.
"""

from __future__ import annotations

import logging
import math
import struct
import threading
from typing import Any, Dict, List, Optional

from backend.handlers.embedding_handler import _get_model
from backend.platform.ai_db import ai_db
from backend.platform.app_db import AppDatabase
from backend.platform.discovery import discover_apps

logger = logging.getLogger(__name__)

# Lazily populated on first search call — maps app_name → AppDatabase instance.
_app_dbs: Dict[str, AppDatabase] | None = None
_app_dbs_lock = threading.Lock()


def _get_app_databases() -> Dict[str, AppDatabase]:
    """Return app_name → AppDatabase mapping, built once at first call (thread-safe)."""
    global _app_dbs
    if _app_dbs is None:
        with _app_dbs_lock:
            if _app_dbs is None:
                _app_dbs = {m.name: AppDatabase(m.db_path) for m in discover_apps()}
                logger.debug("semantic_search: cached %d app databases", len(_app_dbs))
    return _app_dbs


def _decode_vector(vector_bytes: bytes) -> List[float]:
    """Decode raw float32 bytes (struct.pack format) back to a list of floats."""
    return list(struct.unpack(f"{len(vector_bytes) // 4}f", vector_bytes))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity using stdlib only. Returns 0.0 for zero vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def search(
    query: str,
    app_name: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Return the top *limit* items most semantically similar to *query*.

    Searches all apps unless *app_name* is specified. Items deleted after their
    embedding was stored (data is None) are silently excluded from results.

    Returns list of dicts: {app_name, item_id, data: dict, similarity: float}.
    """
    logger.info("semantic_search: query=%r app_name=%s limit=%d", query, app_name, limit)

    query_vector: List[float] = _get_model().encode(query).tolist()
    embeddings = ai_db.list_embeddings(app_name)
    logger.debug("semantic_search: scoring %d embeddings", len(embeddings))

    scored = [
        (_cosine_similarity(query_vector, _decode_vector(row["vector"])),
         row["app_name"], row["item_id"])
        for row in embeddings
    ]
    scored.sort(key=lambda t: t[0], reverse=True)

    app_databases = _get_app_databases()
    results: List[Dict[str, Any]] = []
    for similarity, result_app_name, item_id in scored[:limit]:
        db = app_databases.get(result_app_name)
        if db is None:
            logger.warning("semantic_search: no database for app=%s", result_app_name)
            continue
        data = db.get_item(item_id)
        if data is None:
            continue  # deleted after embedding was stored
        results.append({"app_name": result_app_name, "item_id": item_id,
                        "data": data, "similarity": similarity})

    logger.info("semantic_search: returning %d results", len(results))
    return results
