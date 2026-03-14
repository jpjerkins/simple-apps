# Apps Directory

Each app lives in its own subdirectory: `apps/<name>/`.
The platform discovers apps at startup by scanning for `apps/*/manifest.json`.

---

## Directory Layout

```
apps/
  _template/              ← Copy this to create a new app
    manifest.json         ← App manifest (required)
  todos/
    manifest.json
    router.py             ← FastAPI APIRouter
    frontend/             ← React/Vite source
      src/
      dist/               ← Built assets (volume-mounted, see docker-compose.yml)
      package.json
      vite.config.js
    data/                 ← SQLite database (volume-mounted)
      todos.db
  razorblades/
    manifest.json
    router.py
    frontend/
      dist/
    data/
      razorblades.db
  books/
    manifest.json
    router.py
    frontend/
      dist/
    data/
      books.db
  manifest.schema.json    ← JSON Schema definition for manifest.json
```

---

## manifest.json

Every app directory **must** contain a `manifest.json` that conforms to
`apps/manifest.schema.json`.  The platform validates every manifest at startup
and refuses to load an app with a missing or invalid manifest.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Machine-readable slug. Lowercase, alphanumeric, hyphens/underscores. Must match the directory name. e.g. `"todos"` |
| `label` | string | Human-readable display name shown in the nav bar. e.g. `"To-Do List"` |
| `version` | string | Semantic version `MAJOR.MINOR.PATCH`. e.g. `"1.0.0"` |
| `description` | string | One-sentence description shown on the home page. |
| `db_path` | string | Path to the SQLite file, relative to the repo root. e.g. `"apps/todos/data/todos.db"` |
| `router_module` | string | Python dotted module path that exports a FastAPI `router` object. e.g. `"apps.todos.router"` |
| `frontend_dist` | string | Path to the compiled Vite `dist/` folder, relative to repo root. e.g. `"apps/todos/frontend/dist"` |
| `url_prefix` | string | URL path where the frontend is served. Must start with `/`. e.g. `"/todos"` |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `icon` | string | `""` | Emoji or short string for nav icons. e.g. `"✓"` |
| `api_prefix` | string | `"/api/<name>"` | URL path prefix for REST API endpoints. |
| `events.emits` | string[] | `[]` | Event types this app will publish (future event bus). |
| `events.consumes` | string[] | `[]` | Event types this app subscribes to (future event bus). |
| `metadata` | object | `{}` | Arbitrary app-specific key-value pairs passed to the router at startup. |

### Example

```json
{
  "$schema": "../manifest.schema.json",
  "name": "todos",
  "label": "To-Do List",
  "version": "1.0.0",
  "description": "Simple task tracker for daily todos.",
  "icon": "✓",
  "url_prefix": "/todos",
  "api_prefix": "/api/todos",
  "db_path": "apps/todos/data/todos.db",
  "router_module": "apps.todos.router",
  "frontend_dist": "apps/todos/frontend/dist",
  "events": {
    "emits": ["todos.item.created", "todos.item.completed"],
    "consumes": []
  }
}
```

---

## Adding a New App

1. **Copy the template** — `cp -r apps/_template apps/myapp`
2. **Edit `manifest.json`** — replace every `myapp` placeholder with your app's
   actual name and fill in `label`, `description`, `icon`.
3. **Create `router.py`** — implement a FastAPI `APIRouter`; see
   `apps/todos/router.py` for a reference implementation.
4. **Create the frontend** — scaffold a Vite app under `apps/myapp/frontend/`;
   build and place the output in `apps/myapp/frontend/dist/`.
5. **Ensure `data/` is writable** — the platform creates the SQLite file
   automatically on first run.
6. **Restart the container** — `docker compose restart simple-apps`.
   No platform code changes are needed.

> **Open/Closed guarantee**: the platform scans for manifests at startup and
> mounts each app's router and static files automatically.  Adding a new app
> never requires changes to platform code.

---

## Event Bus (Groundwork)

The `events.emits` and `events.consumes` fields are parsed but not yet acted
upon.  They serve as a formal contract for the planned inter-app event bus.

See `docs/event-bus.md` for the full architecture design.

**Naming convention for event types**: `<app>.<noun>.<verb>`
Examples: `todos.item.created`, `books.item.completed`, `razorblades.blade.retired`

---

## Legacy Schema Files

The files `todos.schema.json`, `razorblades.schema.json`, and
`books.schema.json` in this directory are from the previous generic schema-driven
platform and are kept for reference during migration.  They will be removed once
all three apps have been migrated to the new per-app structure.
