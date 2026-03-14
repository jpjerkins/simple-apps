# Simple Apps Skill — Claude Code

Read and write access to all Simple Apps data from within a Claude Code session.

## Setup

```bash
pip install httpx
```

The skill connects to `http://localhost:8000`. Simple Apps must be running locally.

## Import

```python
from skills.claude_code.simple_apps import (
    search_semantic, find_related,
    list_items, get_item, create_item, update_item, delete_item,
    list_apps,
)
```

## Examples

```python
# Discover what apps exist
apps = list_apps()

# Find books about leadership (semantic, not keyword)
results = search_semantic("leadership management", app_name="books")
# results: [{app_name, item_id, data, similarity}, ...]

# Search across all apps at once
results = search_semantic("stoic philosophy")

# List all books, sorted by title
books = list_items("books", sort_field="title")

# Filter in Python after fetching
unread = [b for b in books if b.get("status") == "to-read"]

# Get a single item
book = get_item("books", item_id=42)  # None if not found

# Create a new item
new_book = create_item("books", {
    "title": "Deep Work",
    "author": "Cal Newport",
    "status": "to-read",
})

# Update an item (full replace)
updated = update_item("books", item_id=42, data={
    "title": "Deep Work",
    "author": "Cal Newport",
    "status": "read",
})

# Delete an item
deleted = delete_item("books", item_id=42)  # True on success

# Find items related to a book (graph traversal)
related = find_related(item_id=42, app_name="books")
related = find_related(item_id=42, app_name="books", relation_type="recommended_by", max_depth=1)
```

## Error Handling

All functions raise `httpx.HTTPStatusError` on non-2xx responses (except `get_item`,
which returns `None` on 404).
