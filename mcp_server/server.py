"""Simple Apps MCP server entry point.

Exposes all Simple Apps data (books, todos, razorblades, etc.) as MCP tools
accessible to Claude Desktop, Claude Code, and the Chrome extension.

Transport: SSE (HTTP) on PORT (default 8003).
Upstream:  SIMPLE_APPS_URL (default http://simple-apps-simple-apps-1:8000).
"""
import os
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import register_tools

_SIMPLE_APPS_URL = os.getenv("SIMPLE_APPS_URL", "http://simple-apps-simple-apps-1:8000")
_PORT = int(os.getenv("PORT", "8003"))

mcp = FastMCP("Simple Apps", host="0.0.0.0", port=_PORT)
register_tools(mcp, _SIMPLE_APPS_URL)

if __name__ == "__main__":
    mcp.run(transport="sse")
