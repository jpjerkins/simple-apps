"""BFS graph traversal over the relationships table in platform-ai.db.

Bounded context: AI / knowledge-graph infrastructure.
Fetches full item data from each app's SQLite DB using the same lazy-cache as semantic_search.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, List, Optional

from backend.platform.ai_db import ai_db
from backend.platform.app_db import AppDatabase
from backend.platform.discovery import discover_apps

logger = logging.getLogger(__name__)

_MAX_DEPTH_CAP = 3

# Lazily populated on first call — maps app_name → AppDatabase.
_app_dbs: Dict[str, AppDatabase] | None = None


def _get_app_databases() -> Dict[str, AppDatabase]:
    """Return app_name → AppDatabase mapping, built once (not thread-safe; acceptable here)."""
    global _app_dbs
    if _app_dbs is None:
        _app_dbs = {m.name: AppDatabase(m.db_path) for m in discover_apps()}
        logger.debug("relationship_queries: cached %d app databases", len(_app_dbs))
    return _app_dbs


def get_related(
    item_id: int,
    app_name: str,
    relation_type: Optional[str] = None,
    max_depth: int = 2,
) -> List[Dict[str, Any]]:
    """BFS from (app_name, item_id); returns reachable items up to max_depth hops (cap: 3).

    Returns list of dicts: {app_name, item_id, data, relation_type, depth}.
    data is None when the app DB is unknown or the record no longer exists.
    """
    effective_depth = min(max_depth, _MAX_DEPTH_CAP)
    app_databases = _get_app_databases()

    visited: set[tuple[str, int]] = {(app_name, item_id)}
    queue: deque[tuple[str, int, int]] = deque([(app_name, item_id, 0)])
    results: List[Dict[str, Any]] = []

    while queue:
        cur_app, cur_id, depth = queue.popleft()
        if depth >= effective_depth:
            continue
        for edge in ai_db.get_relationships(cur_app, cur_id):
            if relation_type and edge["relation_type"] != relation_type:
                continue
            # Walk to the side that is NOT the current node.
            if edge["from_app"] == cur_app and edge["from_item_id"] == cur_id:
                nb_app, nb_id = edge["to_app"], edge["to_item_id"]
            else:
                nb_app, nb_id = edge["from_app"], edge["from_item_id"]
            if (nb_app, nb_id) in visited:
                continue
            visited.add((nb_app, nb_id))
            db = app_databases.get(nb_app)
            data = db.get_item(nb_id) if db is not None else None
            results.append({
                "app_name": nb_app, "item_id": nb_id,
                "data": data, "relation_type": edge["relation_type"], "depth": depth + 1,
            })
            queue.append((nb_app, nb_id, depth + 1))

    logger.info(
        "relationship_queries: get_related app=%s item_id=%d depth=%d found=%d",
        app_name, item_id, effective_depth, len(results),
    )
    return results
