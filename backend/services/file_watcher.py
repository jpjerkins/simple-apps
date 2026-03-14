"""File-system watcher for the Obsidian vault.

Starts a background watchdog observer that fires import_note() for every
.md file that is created or modified in the vault. A per-path 2-second
debounce prevents redundant imports during rapid editor saves.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from backend.services.note_importer import VAULT_PATH, import_note

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0


class _NoteEventHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            with self._lock:
                existing = self._timers.pop(event.src_path, None)
                if existing:
                    existing.cancel()

    def _schedule(self, src_path: str) -> None:
        with self._lock:
            existing = self._timers.pop(src_path, None)
            if existing:
                existing.cancel()
            timer = threading.Timer(_DEBOUNCE_SECONDS, self._fire, args=[src_path])
            self._timers[src_path] = timer
            timer.start()

    def _fire(self, src_path: str) -> None:
        with self._lock:
            self._timers.pop(src_path, None)
        import_note(Path(src_path))


def start_file_watcher() -> None:
    """Start the vault watcher as a daemon thread. Safe to call once at startup."""
    if not VAULT_PATH.exists():
        logger.warning(
            "file_watcher: vault path not found: %s — watcher not started", VAULT_PATH
        )
        return

    observer = Observer()
    observer.schedule(_NoteEventHandler(), str(VAULT_PATH), recursive=True)
    observer.daemon = True
    observer.start()
    logger.info("file_watcher: watching %s", VAULT_PATH)
