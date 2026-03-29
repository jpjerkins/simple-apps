"""Simple Apps tool definitions — registered on the MCP server instance."""
import httpx
from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP, base_url: str) -> None:
    """Register all Simple Apps CRUD and search tools on mcp."""

    def _call(method: str, path: str, **kwargs):
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            r = client.request(method, path, **kwargs)
            r.raise_for_status()
            return r.json()

    def _get_or_none(path: str) -> dict | None:
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            r = client.get(path)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()

    @mcp.tool()
    def list_apps() -> list[dict]:
        """List all available apps with their schema metadata."""
        return _call("GET", "/api/apps")

    @mcp.tool()
    def list_items(app_name: str, sort_field: str = "", sort_order: str = "asc") -> list[dict]:
        """List all items in an app. sort_field is optional."""
        params: dict = {"sort_order": sort_order}
        if sort_field:
            params["sort_field"] = sort_field
        return _call("GET", f"/api/{app_name}/items", params=params)

    @mcp.tool()
    def get_item(app_name: str, item_id: int) -> dict | None:
        """Get a single item by ID. Returns null if not found."""
        return _get_or_none(f"/api/{app_name}/items/{item_id}")

    @mcp.tool()
    def create_item(app_name: str, data: dict) -> dict:
        """Create a new item. data keys must match the app's schema fields."""
        return _call("POST", f"/api/{app_name}/items", json=data)

    @mcp.tool()
    def update_item(app_name: str, item_id: int, data: dict) -> dict:
        """Update an item by ID (full replace). Returns the updated item."""
        return _call("PUT", f"/api/{app_name}/items/{item_id}", json=data)

    @mcp.tool()
    def delete_item(app_name: str, item_id: int) -> bool:
        """Delete an item by ID. Returns true on success."""
        _call("DELETE", f"/api/{app_name}/items/{item_id}")
        return True

    @mcp.tool()
    def search_semantic(query: str, app_name: str = "", limit: int = 10) -> list[dict]:
        """Search items by meaning. Leave app_name empty to search all apps.

        Returns list of: {app_name, item_id, data, similarity}
        """
        payload: dict = {"query": query, "limit": limit}
        if app_name:
            payload["app_name"] = app_name
        return _call("POST", "/api/search/semantic", json=payload)

    @mcp.tool()
    def find_related(
        app_name: str,
        item_id: int,
        relation_type: str = "",
        max_depth: int = 2,
    ) -> list[dict]:
        """Find items related to a given item via graph traversal.

        Returns list of: {app_name, item_id, data, relation_type, depth}
        """
        params: dict = {"max_depth": max_depth}
        if relation_type:
            params["relation_type"] = relation_type
        return _call("GET", f"/api/relationships/{app_name}/{item_id}", params=params)
