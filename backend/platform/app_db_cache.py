"""Shared thread-safe cache of app_name → AppDatabase instances.

Built once on first call via discover_apps(); safe to call from background threads.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict

from backend.platform.app_db import AppDatabase
from backend.platform.discovery import discover_apps

logger = logging.getLogger(__name__)

_app_dbs: Dict[str, AppDatabase] | None = None
_lock = threading.Lock()


def get_app_databases() -> Dict[str, AppDatabase]:
    """Return app_name → AppDatabase mapping, populated once at first call (thread-safe)."""
    global _app_dbs
    if _app_dbs is None:
        with _lock:
            if _app_dbs is None:
                _app_dbs = {m.name: AppDatabase(m.db_path) for m in discover_apps()}
                logger.debug("app_db_cache: cached %d app databases", len(_app_dbs))
    return _app_dbs
