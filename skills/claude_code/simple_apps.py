"""Simple Apps skill for Claude Code.

Gives Claude Code read and write access to all Simple Apps data via HTTP.
Import and call these functions during a Claude Code session.

Usage:
    from skills.claude_code.simple_apps import search_semantic, list_items, ...

Requires: pip install httpx
"""

import httpx

BASE_URL = "http://localhost:8001"


def search_semantic(query: str, app_name: str | None = None, limit: int = 10) -> list[dict]:
    """Search all apps (or one app) by meaning.

    Returns list of: {app_name, item_id, data, similarity}
    """
    response = httpx.post(
        f"{BASE_URL}/api/search/semantic",
        json={"query": query, "app_name": app_name, "limit": limit},
    )
    response.raise_for_status()
    return response.json()


def find_related(
    item_id: int,
    app_name: str,
    relation_type: str | None = None,
    max_depth: int = 2,
) -> list[dict]:
    """Find items related to a given item via graph traversal.

    Returns list of: {app_name, item_id, data, relation_type, depth}
    """
    params: dict = {"max_depth": max_depth}
    if relation_type is not None:
        params["relation_type"] = relation_type
    response = httpx.get(
        f"{BASE_URL}/api/relationships/{app_name}/{item_id}",
        params=params,
    )
    response.raise_for_status()
    return response.json()


def list_items(
    app_name: str,
    sort_field: str | None = None,
    sort_order: str = "asc",
) -> list[dict]:
    """List all items in an app."""
    params: dict = {"sort_order": sort_order}
    if sort_field is not None:
        params["sort_field"] = sort_field
    response = httpx.get(f"{BASE_URL}/api/{app_name}/items", params=params)
    response.raise_for_status()
    return response.json()


def get_item(app_name: str, item_id: int) -> dict | None:
    """Get a single item by ID. Returns None if not found."""
    response = httpx.get(f"{BASE_URL}/api/{app_name}/items/{item_id}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def create_item(app_name: str, data: dict) -> dict:
    """Create a new item. Returns the created item with its assigned ID."""
    response = httpx.post(f"{BASE_URL}/api/{app_name}/items", json=data)
    response.raise_for_status()
    return response.json()


def update_item(app_name: str, item_id: int, data: dict) -> dict:
    """Update an item (full replace). Returns the updated item."""
    response = httpx.put(f"{BASE_URL}/api/{app_name}/items/{item_id}", json=data)
    response.raise_for_status()
    return response.json()


def delete_item(app_name: str, item_id: int) -> bool:
    """Delete an item. Returns True on success."""
    response = httpx.delete(f"{BASE_URL}/api/{app_name}/items/{item_id}")
    response.raise_for_status()
    return True


def list_apps() -> list[dict]:
    """List all available apps with their metadata."""
    response = httpx.get(f"{BASE_URL}/api/apps")
    response.raise_for_status()
    return response.json()
