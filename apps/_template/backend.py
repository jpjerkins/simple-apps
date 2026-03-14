"""Backend router for the myapp app.

Replace 'myapp' throughout with your actual app name.
See apps/todos/backend.py for a complete reference implementation.
"""

from fastapi import APIRouter

router = APIRouter()


# ---------------------------------------------------------------------------
# Routes — add your endpoints here
# ---------------------------------------------------------------------------

@router.get("/")
def list_items():
    """Return all items.  Replace with real DB logic."""
    return []
