# Project Documentation
* This project's documentation is in my notes at the relative path `\1 Projects\Simple Apps`. Please refer to that location for detailed project documentation, notes, and reference materials.
* Always use mermaid syntax for diagrams in documentation.
* Whenever you create a new note, always tag it with the `AI-generated` tag

## Web Research Guidelines

When conducting web research for this project:

- **Include liberal links to original sources**, especially 1st-party documentation (official docs, GitHub repos, etc.)
- **Report when information is NOT found** in a particular area—never fabricate or make up results

## Coding Guidelines

### Schema-Driven Development
- New app = new `.schema.json` file in `/apps` directory
- NEVER modify generic CRUD code for app-specific logic
- All app behavior is defined declaratively in schemas
- Keep schemas self-documenting with clear descriptions and labels

### Single Responsibility
- Each file has one clear job. Planned responsibilities:
  - **Backend:**
    - `backend/main.py` — FastAPI app, API routes only
    - `backend/db.py` — SQLite connection and table initialization only
    - `backend/schema_registry.py` — Schema loading and validation only
    - `backend/crud.py` — Generic database operations only (list, get, create, update, delete)
  - **Frontend:**
    - `frontend/src/App.jsx` — Router setup and schema loading only
    - `frontend/src/ListView.jsx` — Display list view only (no form logic)
    - `frontend/src/FormView.jsx` — Edit/create forms only (no list logic)
    - `frontend/src/components/FieldRenderer.jsx` — Render individual fields only
    - `frontend/src/components/Navbar.jsx` — Navigation UI only
    - `frontend/src/styles.css` — All visual styling
- If a file gains a second responsibility, split it before adding more code.

### File and Function Size
- Python files: aim for under 150 lines; 200 is the hard limit before splitting.
- JS files: aim for under 400 lines; split at 500.
- Functions: ideally under 20 lines. Extract helpers rather than growing a function.
- If a function needs more than one level of nesting to explain what it does, it should be split.

### Naming Conventions
- **Python**: `snake_case` for everything. Prefix module-private names with `_` (e.g. `_validate_schema`, `_DB_PATH`). Public API is unprefixed.
- **JavaScript**: `camelCase` for functions and variables, `PascalCase` for React components.
- **Schema IDs**: lowercase, no spaces (e.g. `books`, `razorblades`, `carmaintenance`)
- **Field IDs**: camelCase (e.g. `startDate`, `licensePlate`, `usageCount`)
- Names should be descriptive and self-documenting. Avoid abbreviations except established ones (`db`, `id`, `api`).

### Mobile-First Requirement
ALL UI components must be mobile-friendly:
- Use responsive CSS (mobile base styles, media queries for larger screens)
- Touch-friendly tap targets (minimum 44px)
- Test on mobile viewport (375px width minimum)
- No horizontal scrolling on small screens
- Progressive enhancement for tablets and desktop

### Open/Closed Principle
- Extend functionality by adding new schemas, NOT by modifying existing code
- Generic components should work with ANY valid schema
- If you find yourself adding app-specific logic to generic code, you're doing it wrong

### Process
- After completing each phase, run `/simplify` to review the changed code for quality, reuse, and SRP, then fix issues found.
- Don't add abstractions speculatively. Extract only when a pattern appears at least twice, or when a function/file exceeds the size guidelines.
- Test mobile layout for every new feature

## Adding a New App

Follow this checklist when adding a new app:

1. Create `/apps/your-app.schema.json` with all required fields
2. Validate schema structure (id, name, fields array)
3. Define field types, labels, and validation rules
4. Set display options (displayInList, filter, sortable)
5. Configure default sort and views
6. Restart container to load new schema
7. Test on mobile viewport
8. **No code changes should be needed**

## Data Migration

When migrating data from TiddlyWiki or other sources:

- Create migration script in `/scripts/migrate_*.py`
- Validate data against schema before insertion
- Handle missing/optional fields gracefully
- Log any data transformation decisions
- Keep original data as backup until migration verified
