"""Extract and store relationships between items on item.created/item.updated events.

Bounded context: AI / knowledge-graph infrastructure.
INSERT OR IGNORE makes re-runs safe. Handlers never propagate exceptions.
"""

from __future__ import annotations

import logging

from backend.platform.ai_db import ai_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App-specific extraction rules
# ---------------------------------------------------------------------------

def _extract_books(item_id: int, item_data: dict) -> None:
    """Store recommended_by edge for books with a non-empty recommendedBy field."""
    name = item_data.get("recommendedBy", "")
    if name:
        ai_db.insert_relationship(
            from_app="books", from_item_id=item_id,
            to_app="contacts", to_item_id=0,  # placeholder until contacts app exists
            relation_type="recommended_by", metadata={"name": name},
        )
        logger.debug("relationship_handler: books/%d recommended_by=%r", item_id, name)


def _extract_todos(item_id: int, item_data: dict) -> None:
    """Store part_of edge for todos with a non-empty project field."""
    project = item_data.get("project", "")
    if project:
        ai_db.insert_relationship(
            from_app="todos", from_item_id=item_id,
            to_app="projects", to_item_id=0,  # placeholder until projects app exists
            relation_type="part_of", metadata={"project_name": project},
        )
        logger.debug("relationship_handler: todos/%d part_of=%r", item_id, project)


_EXTRACTORS = {
    "books": _extract_books,
    "todos": _extract_todos,
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _extract_relationships(event_name: str, payload: dict) -> None:
    """Route payload to the correct app extractor (no-op if none registered)."""
    app_name = event_name.split(".")[0]
    extractor = _EXTRACTORS.get(app_name)
    if extractor is not None:
        extractor(payload["id"], payload)


# ---------------------------------------------------------------------------
# Public event handlers
# ---------------------------------------------------------------------------

def handle_item_created(event_name: str, payload: dict) -> None:
    """Handle <app>.item.created — extract and store relationships."""
    try:
        _extract_relationships(event_name, payload)
    except Exception:
        logger.exception("relationship_handler: error processing %r", event_name)


def handle_item_updated(event_name: str, payload: dict) -> None:
    """Handle <app>.item.updated — re-extract relationships (duplicates ignored)."""
    try:
        _extract_relationships(event_name, payload)
    except Exception:
        logger.exception("relationship_handler: error processing %r", event_name)
