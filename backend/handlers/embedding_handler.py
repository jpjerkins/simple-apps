"""Event handlers that generate and persist semantic embeddings for app items.

Bounded context: AI / semantic search infrastructure.

When an item is created or updated in any app, the event bus calls
``handle_item_created`` or ``handle_item_updated``. These handlers generate a
text representation of the item, encode it as a float32 embedding using
``sentence-transformers``, and persist it in the platform AI database.

The ``SentenceTransformer`` model is lazy-loaded on first use to keep import
time fast. It is then cached as a module-level singleton for all subsequent
calls (model loading takes ~1 second on first call).

Handler design rule: all public handlers MUST catch all exceptions and log
them without re-raising, so the event bus error-isolation guarantee holds.
"""

from __future__ import annotations

import logging
import struct
import threading

from backend.platform.ai_db import ai_db

logger = logging.getLogger(__name__)

# Lazy singleton — loaded on first encode call, not at import time.
# Lock ensures only one thread loads the model even if concurrent events arrive.
_model = None
_model_lock = threading.Lock()
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    """Return the cached SentenceTransformer, loading it on first call (thread-safe)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-checked locking
                logger.info("embedding_handler: loading model %r", _MODEL_NAME)
                from sentence_transformers import SentenceTransformer  # noqa: PLC0415
                _model = SentenceTransformer(_MODEL_NAME)
                logger.info("embedding_handler: model loaded")
    return _model


# ---------------------------------------------------------------------------
# Text representation builders
# ---------------------------------------------------------------------------

def create_embedding_text(app_name: str, item_data: dict) -> str:
    """Build a human-readable text string that captures the semantics of an item.

    Each app has a tailored template; unknown apps fall back to joining all
    string-valued fields so new apps work automatically without code changes.
    """
    if app_name == "books":
        return (
            f"Book: {item_data.get('title', '')} by {item_data.get('author', '')}."
            f" Category: {item_data.get('category', '')}."
            f" {item_data.get('notes', '')}"
        )
    if app_name == "razorblades":
        return (
            f"Razor blade: {item_data.get('brand', '')}."
            f" Uses: {item_data.get('useCount', '')}."
            f" Notes: {item_data.get('notes', '')}"
        )
    if app_name == "todos":
        return f"Task: {item_data.get('title', '')}. {item_data.get('description', '')}"
    if app_name == "notes":
        title = item_data.get("title", "")
        tags = " ".join(item_data.get("tags") or [])
        content = item_data.get("content", "")
        return f"{title}. Tags: {tags}. {content}"
    # Generic fallback — join all string field values
    string_values = [str(v) for v in item_data.values() if isinstance(v, str) and v]
    return " ".join(string_values)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def _encode_vector(vector) -> bytes:
    """Encode a float sequence as raw float32 bytes (little-endian)."""
    return struct.pack(f"{len(vector)}f", *vector)


# ---------------------------------------------------------------------------
# Core generation logic
# ---------------------------------------------------------------------------

def _generate_and_store(app_name: str, item_id: int, item_data: dict) -> None:
    """Generate an embedding for item_data and persist it in the AI database.

    Raises nothing — all exceptions are caught and logged.
    """
    try:
        text = create_embedding_text(app_name, item_data)
        model = _get_model()
        raw_vector = model.encode(text)
        vector_bytes = _encode_vector(raw_vector)
        ai_db.upsert_embedding(app_name, item_id, vector_bytes, _MODEL_NAME)
        logger.debug(
            "embedding_handler: stored embedding app=%s item_id=%d text_len=%d",
            app_name, item_id, len(text),
        )
    except Exception:
        logger.exception(
            "embedding_handler: failed to generate embedding app=%s item_id=%d",
            app_name, item_id,
        )


# ---------------------------------------------------------------------------
# Public event handlers
# ---------------------------------------------------------------------------

def _handle_upsert_event(event_name: str, payload: dict) -> None:
    """Shared logic for item.created and item.updated — generate or refresh an embedding."""
    try:
        app_name = event_name.split(".")[0]
        item_id = payload["id"]
        _generate_and_store(app_name, item_id, payload)
    except Exception:
        logger.exception("embedding_handler: error processing %r", event_name)


def handle_item_created(event_name: str, payload: dict) -> None:
    """Handle ``<app>.item.created`` — generate and store an embedding."""
    _handle_upsert_event(event_name, payload)


def handle_item_updated(event_name: str, payload: dict) -> None:
    """Handle ``<app>.item.updated`` — regenerate and overwrite the embedding."""
    _handle_upsert_event(event_name, payload)


def handle_item_deleted(event_name: str, payload: dict) -> None:
    """Handle ``<app>.item.deleted`` — remove the embedding from the AI database."""
    try:
        app_name = event_name.split(".")[0]
        item_id = payload["id"]
        deleted = ai_db.delete_embedding(app_name, item_id)
        logger.debug(
            "embedding_handler: deleted embedding app=%s item_id=%d found=%s",
            app_name, item_id, deleted,
        )
    except Exception:
        logger.exception("embedding_handler: error in handle_item_deleted for %r", event_name)
