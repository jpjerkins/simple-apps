---
name: simple-apps
description: Access Phil's personal data apps — reading list, razor blade tracker, todos, and Obsidian notes. Use when Phil asks about books, what he's reading, tasks, razors, or wants to search or update his personal data.
---

# Simple Apps

Personal data platform. Stores books, razor blades, todos, and notes (read-only, from Obsidian vault) in a local API with semantic search and graph traversal.

**Base URL:** `http://thejerkins.duckdns.org:8001`

## When to Use

- Phil mentions books, reading list, what he's reading, recommendations
- Phil mentions razors, blades, shaving, use count
- Phil mentions todos, tasks, to-do list (the simple-apps version, not Obsidian)
- Phil wants to search across his personal data by meaning
- Phil wants to find connections between items

**Do NOT use for Obsidian notes** — access those directly via filesystem (Grep/Read/Write). The `notes` app in simple-apps is read-only and less capable than direct access.

## API Reference

All calls use `curl` from Bash.

### List available apps

```bash
curl -s http://thejerkins.duckdns.org:8001/api/apps | python3 -m json.tool
```

### List items in an app

```bash
curl -s "http://thejerkins.duckdns.org:8001/api/{app_name}/items?sort_field={field}&sort_order=asc" | python3 -m json.tool
```

Apps: `books`, `razorblades`, `todos`, `notes`

### Get a single item

```bash
curl -s http://thejerkins.duckdns.org:8001/api/{app_name}/items/{id} | python3 -m json.tool
```

### Semantic search (search by meaning)

```bash
# Across all apps:
curl -s -X POST http://thejerkins.duckdns.org:8001/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "stoicism philosophy", "limit": 5}' | python3 -m json.tool

# Within one app:
curl -s -X POST http://thejerkins.duckdns.org:8001/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "blade longevity", "app_name": "razorblades", "limit": 5}' | python3 -m json.tool
```

Returns: `[{app_name, item_id, data, similarity}]`

### Find related items (graph traversal)

```bash
curl -s "http://thejerkins.duckdns.org:8001/api/relationships/{app_name}/{id}?max_depth=2" | python3 -m json.tool
```

### Create an item

```bash
curl -s -X POST http://thejerkins.duckdns.org:8001/api/{app_name}/items \
  -H "Content-Type: application/json" \
  -d '{"title": "...", "author": "..."}' | python3 -m json.tool
```

### Update an item (full replace)

```bash
curl -s -X PUT http://thejerkins.duckdns.org:8001/api/{app_name}/items/{id} \
  -H "Content-Type: application/json" \
  -d '{"title": "...", "author": "...", "status": "read"}' | python3 -m json.tool
```

### Delete an item

```bash
curl -s -X DELETE http://thejerkins.duckdns.org:8001/api/{app_name}/items/{id}
```

## App Field Reference

| App | Key fields |
|-----|-----------|
| **books** | title, author, category, status (want-to-read / reading / completed), notes, rating, startDate, endDate, recommendedBy |
| **razorblades** | brand, model, purchaseDate, useCount, retireDate, notes |
| **todos** | title, description, status (todo / in-progress / done), priority (low / medium / high), dueDate, project |
| **notes** | path, title, tags, content — **read-only**, imported from Obsidian vault |

## Notes

- `notes` app is read-only (populated automatically from the Obsidian vault). Prefer direct filesystem access for notes.
- Semantic search uses sentence embeddings — natural language queries work well.
- All items return `id`, `created_at`, `updated_at` alongside their fields.
- When updating, send ALL fields (full replace), not just the changed ones. Read the item first, modify, then PUT the full object back.
