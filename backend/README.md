# Backend

FastAPI server providing generic CRUD API for all apps.

## Architecture

**Schema-driven**: All logic is generic and works with any valid schema. No app-specific code.

## Files

- **`main.py`** (~100 lines) - FastAPI app, API routes, static file serving
- **`db.py`** (~40 lines) - SQLite connection management, table initialization
- **`schema_registry.py`** (~60 lines) - Load and validate schemas from `/apps`
- **`crud.py`** (~80 lines) - Generic CRUD operations (list, get, create, update, delete)

**Total:** ~280 lines of Python

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
