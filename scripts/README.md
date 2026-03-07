# Migration Scripts

Python scripts for migrating data from TiddlyWiki notes and other sources.

## Scripts

### Phase 2: Razor Blade Tracker
**`migrate_razors.py`** (~50 lines)
- Reads `Razor started *.md` files from Notes
- Parses frontmatter `list` field (space-separated dates)
- Transforms to schema format
- Inserts into SQLite via API

### Phase 4: Cars
**`migrate_cars.py`** (~80 lines)
- **Pass 1**: Read all car notes (tagged `Car`)
  - Parse frontmatter (VIN, license plate, etc.)
  - Extract year/make/model from filename
  - Insert into `cars` app
- **Pass 2**: For each car, find child notes (tagged with car name)
  - Insert into `carmaintenance` app with `carId` reference

## Usage Pattern

```python
#!/usr/bin/env python3
import json
import requests
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000/api"
NOTES_PATH = Path(r"C:\Users\PhilJ\Nextcloud\Notes")

def migrate():
    # Read source files
    # Transform data
    # Validate against schema
    # Insert via API
    pass

if __name__ == "__main__":
    migrate()
```

## Best Practices

- Always validate data against schema before insertion
- Handle missing/optional fields gracefully
- Log all transformations and errors
- Keep original data as backup until migration verified
- Use API endpoints (not direct DB access) for consistency

## Testing

Test migrations against local instance first:

```bash
# Start local server
docker-compose up

# Run migration script
python scripts/migrate_razors.py

# Verify in UI
open http://localhost:8000
```

## Data Backup

Before running any migration:
```bash
cp data/simple-apps.db data/simple-apps.db.backup
```
