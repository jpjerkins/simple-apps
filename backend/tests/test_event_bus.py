"""Tests for the in-process event bus stub."""

import sys
import os

# Allow running directly without package install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import event_bus


def setup_function():
    """Clear subscriptions between tests."""
    event_bus.clear()


# ---------------------------------------------------------------------------
# Subscribe / unsubscribe
# ---------------------------------------------------------------------------

def test_subscribe_registers_handler():
    called = []

    def handler(name, payload):
        called.append((name, payload))

    event_bus.subscribe("app.event", handler)
    assert handler in event_bus.subscribers("app.event")


def test_unsubscribe_removes_handler():
    def handler(name, payload):
        pass

    event_bus.subscribe("app.event", handler)
    removed = event_bus.unsubscribe("app.event", handler)

    assert removed is True
    assert handler not in event_bus.subscribers("app.event")


def test_unsubscribe_nonexistent_returns_false():
    def handler(name, payload):
        pass

    result = event_bus.unsubscribe("app.event", handler)
    assert result is False


def test_subscribe_non_callable_raises():
    try:
        event_bus.subscribe("app.event", "not_a_function")
        assert False, "Expected TypeError"
    except TypeError:
        pass


# ---------------------------------------------------------------------------
# Publish (stub mode — handlers registered but not called)
# ---------------------------------------------------------------------------

def test_publish_returns_zero_while_stubbed():
    called = []

    def handler(name, payload):
        called.append(name)

    event_bus.subscribe("app.event", handler)
    count = event_bus.publish("app.event", {"key": "value"})

    assert count == 0
    assert called == [], "Stub should NOT invoke handlers"


def test_publish_with_no_subscribers_returns_zero():
    count = event_bus.publish("unknown.event", {"x": 1})
    assert count == 0


def test_publish_with_none_payload_defaults_to_empty_dict():
    # Should not raise
    count = event_bus.publish("app.event", None)
    assert count == 0


def test_publish_with_no_payload_argument():
    count = event_bus.publish("app.event")
    assert count == 0


# ---------------------------------------------------------------------------
# Dispatch (activated future behaviour — tested in isolation)
# ---------------------------------------------------------------------------

def test_dispatch_calls_all_handlers():
    results = []

    def h1(name, payload):
        results.append(("h1", name, payload))

    def h2(name, payload):
        results.append(("h2", name, payload))

    count = event_bus._dispatch("app.event", {"id": 1}, [h1, h2])

    assert count == 2
    assert ("h1", "app.event", {"id": 1}) in results
    assert ("h2", "app.event", {"id": 1}) in results


def test_dispatch_continues_after_handler_exception():
    results = []

    def bad_handler(name, payload):
        raise RuntimeError("boom")

    def good_handler(name, payload):
        results.append("good")

    count = event_bus._dispatch("app.event", {}, [bad_handler, good_handler])

    assert count == 1  # only good_handler succeeded
    assert results == ["good"]


# ---------------------------------------------------------------------------
# Subscribers snapshot
# ---------------------------------------------------------------------------

def test_subscribers_returns_copy():
    def h(name, payload):
        pass

    event_bus.subscribe("app.event", h)
    snap = event_bus.subscribers("app.event")
    snap.append("extra")  # mutate snapshot

    # Original registry should be unaffected
    assert "extra" not in event_bus.subscribers("app.event")


def test_subscribers_empty_for_unknown_event():
    assert event_bus.subscribers("no.such.event") == []


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def test_clear_removes_all_subscriptions():
    event_bus.subscribe("a.b", lambda n, p: None)
    event_bus.subscribe("c.d", lambda n, p: None)
    event_bus.clear()

    assert event_bus.subscribers("a.b") == []
    assert event_bus.subscribers("c.d") == []


if __name__ == "__main__":
    # Simple test runner without pytest dependency
    import traceback

    tests = [
        test_subscribe_registers_handler,
        test_unsubscribe_removes_handler,
        test_unsubscribe_nonexistent_returns_false,
        test_subscribe_non_callable_raises,
        test_publish_returns_zero_while_stubbed,
        test_publish_with_no_subscribers_returns_zero,
        test_publish_with_none_payload_defaults_to_empty_dict,
        test_publish_with_no_payload_argument,
        test_dispatch_calls_all_handlers,
        test_dispatch_continues_after_handler_exception,
        test_subscribers_returns_copy,
        test_subscribers_empty_for_unknown_event,
        test_clear_removes_all_subscriptions,
    ]

    passed = 0
    failed = 0
    for test in tests:
        event_bus.clear()
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {test.__name__}: {exc}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
