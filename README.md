# Simple Apps Platform

A schema-driven platform for hosting multiple simple data-tracking applications in a single Docker container.

## Overview

This platform allows you to create new data-tracking apps by simply defining a JSON schema file—no code changes required. Built with FastAPI (backend) and React (frontend), deployed to Raspberry Pi 5.

**Design Principles:**
- Schema-driven: Extend via configuration, not code
- SOLID principles: Especially SRP and Open/Closed
- Mobile-first: All UI optimized for phone/tablet
- Simple: SQLite database, single Docker container
- Internal-only: No authentication needed

## Documentation

Full project documentation is located in Notes at `\1 Projects\Simple Apps`:
- **Architecture.md** - System design and technical decisions
- **Implementation Plan.md** - Phased development roadmap
- **Schema Examples.md** - Reference schemas for all field types
- **TiddlyWiki Data Analysis.md** - Migration planning from existing notes

## Project Structure

```
simple-apps/
├── backend/              # FastAPI server
│   ├── main.py          # API routes
│   ├── crud.py          # Generic CRUD operations
│   ├── schema_registry.py  # Schema loader
│   └── db.py            # SQLite connection
├── frontend/            # React SPA
│   ├── src/
│   │   ├── App.jsx      # Router and schema loading
│   │   ├── ListView.jsx # Generic list component
│   │   ├── FormView.jsx # Generic form component
│   │   └── components/  # Reusable UI components
│   └── public/
├── apps/                # Schema definitions (*.schema.json)
├── scripts/             # Migration scripts
├── data/                # SQLite database (not in git)
├── docker-compose.yml
├── Dockerfile
└── CLAUDE.md           # Coding guidelines
```

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- SQLite3 (JSON columns for flexibility)
- Uvicorn (ASGI server)

**Frontend:**
- React 18+
- React Router (client-side routing)
- Native CSS (mobile-first, responsive)
- Vite (build tool)

**Infrastructure:**
- Docker (single container deployment)
- Nginx (reverse proxy with HTTPS)
- Let's Encrypt (SSL certificate)
- DuckDNS (subdomain: apps.thejerkins.duckdns.org)

## Quick Start

*(Coming in Phase 1)*

```bash
# Build and run locally
docker-compose up --build

# Access at http://localhost:8000
```

## Adding a New App

1. Create `apps/myapp.schema.json`:

```json
{
  "id": "myapp",
  "name": "My App",
  "icon": "📝",
  "description": "Description of my app",
  "fields": [
    {
      "id": "title",
      "type": "text",
      "label": "Title",
      "required": true,
      "displayInList": true
    }
  ],
  "defaultSort": {
    "field": "title",
    "order": "asc"
  }
}
```

2. Restart container
3. New app appears in navigation automatically

See **Schema Examples.md** in Notes for complete field type reference.

## Planned Apps

- **To-Do List** (Phase 1 - minimal shell example)
- **Razor Blade Tracker** (Phase 2)
- **Books** (Phase 3)
- **Cars** + **Car Maintenance** (Phase 4)
- **Movies to Watch** (Phase 5)
- **Prayer Requests** (Phase 5)

## Development Status

**Current Phase:** Planning Complete

**Next Steps:**
1. Initialize Git repository
2. Create project structure
3. Implement Phase 1 (minimal shell)

## License

Private/Personal Use

---

**See CLAUDE.md for coding guidelines and documentation location.**
