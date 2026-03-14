"""In-process event bus for inter-app communication.

This module provides a publish/subscribe interface for apps to communicate
without direct coupling. Currently a stub — events are logged but not routed.

## Architecture

The event bus is an in-process singleton. Apps publish named events with a
payload dict; other apps subscribe by event name and receive a handler callback.

### Future Work

When inter-app event routing is needed:
- Replace ``_dispatch`` with actual handler invocation.
- Consider async delivery (``asyncio.create_task``) to avoid blocking publishers.
- Add persistence (SQLite event log) for replay/auditing.
- Add dead-letter handling for failed handlers.

### Adding a New Event

1. Define a constant in your app's router module, e.g.::

       EVENT_ITEM_CREATED = "todos.item_created"

2. Publish after the operation succeeds::

       from backend.event_bus import publish
       publish("todos.item_created", {"id": new_id, "title": title})

3. Subscribe in any app's router (call at import time)::

       from backend.event_bus import subscribe
       subscribe("todos.item_created", _handle_todo_created)

### Event Naming Convention

``<app_name>.<verb>_<noun>``  — all lowercase, underscores, dot separator.

Examples: ``todos.item_created``, ``books.item_deleted``, ``razorblades.item_updated``
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[str, Dict[str, Any]], None]

# Registry: event_name -> list of handler callables
_subscribers: Dict[str, List[EventHandler]] = defaultdict(list)


def subscribe(event_name: str, handler: EventHandler) -> None:
    """Register *handler* to be called when *event_name* is published.

    Args:
        event_name: Dot-separated event identifier, e.g. ``"todos.item_created"``.
        handler: Callable with signature ``(event_name: str, payload: dict) -> None``.
                 Exceptions raised by the handler are caught and logged; they do
                 not prevent other handlers or the publisher from completing.

    Example::

        def _on_todo_created(event_name: str, payload: dict) -> None:
            print(f"New todo: {payload['title']}")

        subscribe("todos.item_created", _on_todo_created)
    """
    if not callable(handler):
        raise TypeError(f"handler must be callable, got {type(handler)!r}")
    _subscribers[event_name].append(handler)
    logger.debug("event_bus: subscribed %r to %r", handler.__qualname__, event_name)


def unsubscribe(event_name: str, handler: EventHandler) -> bool:
    """Remove a previously registered handler.

    Args:
        event_name: The event name passed to :func:`subscribe`.
        handler: The exact callable previously registered.

    Returns:
        ``True`` if the handler was found and removed, ``False`` otherwise.
    """
    try:
        _subscribers[event_name].remove(handler)
        logger.debug("event_bus: unsubscribed %r from %r", handler.__qualname__, event_name)
        return True
    except ValueError:
        return False


def publish(event_name: str, payload: Dict[str, Any] | None = None) -> int:
    """Publish an event to all registered subscribers.

    Currently a stub: events are logged but handlers are not yet invoked.
    Remove the early-return stub comment below and enable ``_dispatch`` when
    real inter-app routing is desired.

    Args:
        event_name: Dot-separated event identifier, e.g. ``"todos.item_created"``.
        payload: Arbitrary dict of event data. Defaults to empty dict.

    Returns:
        Number of handlers that were notified (0 while stubbed).

    Example::

        publish("todos.item_created", {"id": 42, "title": "Buy milk"})
    """
    if payload is None:
        payload = {}

    handlers = _subscribers.get(event_name, [])
    handler_count = len(handlers)

    logger.info(
        "event_bus: published %r with %d subscriber(s) | payload keys: %s",
        event_name,
        handler_count,
        list(payload.keys()),
    )

    # --- STUB: handler dispatch disabled until inter-app routing is needed ---
    # When ready to activate, remove this comment block and call _dispatch:
    #
    #   return _dispatch(event_name, payload, handlers)
    #
    # Until then, handlers are registered but never called.
    # -------------------------------------------------------------------------

    return 0  # stub: no handlers invoked yet


def _dispatch(event_name: str, payload: Dict[str, Any], handlers: List[EventHandler]) -> int:
    """Invoke all handlers for an event, catching individual failures.

    This function exists for future activation — it is not called by
    :func:`publish` while the bus is in stub mode.

    Args:
        event_name: Event identifier forwarded to each handler.
        payload: Event payload forwarded to each handler.
        handlers: List of callables to invoke.

    Returns:
        Number of handlers successfully invoked.
    """
    notified = 0
    for handler in handlers:
        try:
            handler(event_name, payload)
            notified += 1
        except Exception:
            logger.exception(
                "event_bus: handler %r raised an exception for event %r",
                handler.__qualname__,
                event_name,
            )
    return notified


def subscribers(event_name: str) -> List[EventHandler]:
    """Return a snapshot of handlers registered for *event_name*.

    Useful for introspection and testing.

    Args:
        event_name: Event name to query.

    Returns:
        Shallow copy of the handler list (safe to iterate while subscribing).
    """
    return list(_subscribers.get(event_name, []))


def clear() -> None:
    """Remove all subscriptions.

    Intended for use in tests only. Do not call in production code.
    """
    _subscribers.clear()
    logger.debug("event_bus: all subscriptions cleared")
