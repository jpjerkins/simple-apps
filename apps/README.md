# Apps Directory

This directory contains schema definitions for all apps in the platform.

## Schema Files

Each app is defined by a JSON file: `<app-id>.schema.json`

**Naming convention:**
- Lowercase, no spaces
- Example: `books.schema.json`, `razorblades.schema.json`, `carmaintenance.schema.json`

## Schema Structure

See `Schema Examples.md` in project documentation (Notes) for complete reference.

**Minimum required fields:**
```json
{
  "id": "appid",
  "name": "Display Name",
  "icon": "📝",
  "description": "Brief description",
  "fields": [
    {
      "id": "fieldId",
      "type": "text",
      "label": "Field Label",
      "required": true
    }
  ]
}
```

## Adding a New App

1. Create `<app-id>.schema.json` in this directory
2. Define all fields with types and validation
3. Set display options (displayInList, filter, sortable)
4. Restart container
5. New app appears in navigation automatically

**No code changes needed!**

## Current Apps

*(Will be populated as apps are added)*

- Phase 1: `todos.schema.json` - To-Do List (example)
- Phase 2: `razorblades.schema.json` - Razor Blade Tracker
- Phase 3: `books.schema.json` - Books to Read
- Phase 4: `cars.schema.json`, `carmaintenance.schema.json` - Vehicle tracking
- Phase 5+: Additional apps as needed
