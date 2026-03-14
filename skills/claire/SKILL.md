---
name: simple-apps
description: Access Phil's personal data apps — reading list, razor blade tracker, todos, and Obsidian notes. Use when Phil asks about books, what he's reading, tasks, notes, or wants to search or update his personal data.
---

# Simple Apps

Personal data platform at `http://localhost:8001`. Stores books, razor blades, todos, and notes in a local API with semantic search.

## List available apps

```bash
curl -s http://localhost:8001/api/apps | jq .
```

## List items in an app

```bash
curl -s "http://localhost:8001/api/books/items?sort_field=title&sort_order=asc" | jq .
```

Apps: `books`, `razorblades`, `todos`, `notes`

## Get a single item

```bash
curl -s http://localhost:8001/api/{app_name}/items/{id} | jq .
```

## Semantic search (search by meaning)

```bash
# Across all apps:
curl -s -X POST http://localhost:8001/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "stoicism philosophy", "limit": 5}' | jq .

# Within one app:
curl -s -X POST http://localhost:8001/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "blade longevity", "app_name": "razorblades", "limit": 5}' | jq .
```

Returns: `[{app_name, item_id, data, similarity}]`

## Find related items (graph traversal)

```bash
curl -s "http://localhost:8001/api/relationships/{app_name}/{id}?max_depth=2" | jq .
```

## Create an item

```bash
curl -s -X POST http://localhost:8001/api/{app_name}/items \
  -H "Content-Type: application/json" \
  -d '{"title": "...", "author": "..."}' | jq .
```

## Update an item (full replace)

```bash
curl -s -X PUT http://localhost:8001/api/{app_name}/items/{id} \
  -H "Content-Type: application/json" \
  -d '{"title": "...", "author": "..."}' | jq .
```

## Delete an item

```bash
curl -s -X DELETE http://localhost:8001/api/{app_name}/items/{id}
```

## App field reference

| App | Key fields |
|-----|-----------|
| **books** | title, author, category, status (want-to-read/reading/completed), notes, rating, startDate, endDate, recommendedBy |
| **razorblades** | brand, model, purchaseDate, useCount, retireDate, notes |
| **todos** | title, description, status (todo/in-progress/done), priority (low/medium/high), dueDate, project |
| **notes** | path, title, tags, content — read-only, imported from Obsidian vault |

## Notes

- `notes` app is read-only (populated automatically from the Obsidian vault)
- Semantic search uses sentence embeddings — natural language queries work well
- All items return `id`, `created_at`, `updated_at` alongside their fields
