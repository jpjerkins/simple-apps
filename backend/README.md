# Backend

FastAPI server providing generic CRUD API for all apps.

## Architecture

**Schema-driven**: All logic is generic and works with any valid schema. No app-specific code.

## Files

- **`main.py`** (~100 lines) - FastAPI app, API routes, static file serving
- **`db.py`** (~40 lines) - SQLite connection management, table initialization
- **`schema_registry.py`** (~60 lines) - Load and validate schemas from `/apps`
- **`crud.py`** (~80 lines) - Generic CRUD operations (list, get, create, update, delete)
- **`event_bus.py`** (~170 lines) - In-process publish/subscribe event bus (stub)

**Total:** ~450 lines of Python

## Event Bus

`event_bus.py` provides a publish/subscribe interface for future inter-app communication.

**Current status: stub** — events are logged but handlers are not invoked. The `_dispatch`
function is implemented and tested; activate it in `publish()` when cross-app routing is needed.

### Quick usage

```python
from backend.event_bus import publish, subscribe

# Publisher (e.g. in todos router after creating an item):
publish("todos.item_created", {"id": new_id, "title": title})

# Subscriber (e.g. in another app's router at import time):
def _on_todo_created(event_name: str, payload: dict) -> None:
    ...

subscribe("todos.item_created", _on_todo_created)
```

### Event naming convention

`<app_name>.<verb>_<noun>` — e.g. `todos.item_created`, `books.item_deleted`

### Tests

```bash
python backend/tests/test_event_bus.py
```

## API Endpoints

```
GET  /api/schemas                    - List all app schemas
GET  /api/{app_id}/items             - List items (with optional filters/sort)
GET  /api/{app_id}/items/{item_id}   - Get single item
POST /api/{app_id}/items             - Create item
PUT  /api/{app_id}/items/{item_id}   - Update item
DELETE /api/{app_id}/items/{item_id} - Delete item
```

Static files (frontend) served from `/`

## Dependencies

```
fastapi
uvicorn
sqlite3 (built-in)
pydantic (included with FastAPI)
```

## Running Locally

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## Testing

```bash
# List schemas
curl http://localhost:8000/api/schemas

# Create item
curl -X POST http://localhost:8000/api/todos/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "status": "pending"}'

# List items
curl http://localhost:8000/api/todos/items
```

## Code Guidelines

- Each file has one responsibility (see CLAUDE.md)
- Max 150 lines per file (200 hard limit)
- Use snake_case for everything
- Prefix private functions with `_`
- No app-specific logic - all operations are generic
