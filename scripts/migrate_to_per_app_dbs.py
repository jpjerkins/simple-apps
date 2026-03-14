"""Migrate data from the old shared simple-apps.db to per-app SQLite databases.

Source:  /mnt/data/simple-apps/simple-apps.db  (table: app_items)
Targets: apps/<name>/data/<name>.db             (table: items)

The data format is identical — both tables store a JSON blob in a 'data'
column — so this is a direct row copy, preserving created_at / updated_at.

Usage:
    python3 scripts/migrate_to_per_app_dbs.py [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SOURCE_DB = Path("/mnt/data/simple-apps/simple-apps.db")

# Map app_id -> target database path
TARGETS: dict[str, Path] = {
    "books":       REPO_ROOT / "apps/books/data/books.db",
    "razorblades": REPO_ROOT / "apps/razorblades/data/razorblades.db",
    "todos":       REPO_ROOT / "apps/todos/data/todos.db",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    uri = f"file:{path}{'?mode=ro' if readonly else ''}{'&' if readonly else '?'}uri=true"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            data       TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _target_is_empty(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT COUNT(*) FROM items").fetchone()
    return row[0] == 0


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

def migrate(dry_run: bool = False) -> None:
    if not SOURCE_DB.exists():
        print(f"[ERROR] Source database not found: {SOURCE_DB}", file=sys.stderr)
        sys.exit(1)

    src = _connect(SOURCE_DB, readonly=True)

    totals = {"copied": 0, "skipped": 0}

    for app_id, target_path in TARGETS.items():
        rows = src.execute(
            "SELECT data, created_at, updated_at FROM app_items WHERE app_id = ? ORDER BY id",
            (app_id,),
        ).fetchall()

        if not rows:
            print(f"  [{app_id}] no rows in source — skipping")
            totals["skipped"] += 1
            continue

        print(f"  [{app_id}] {len(rows)} row(s) to migrate → {target_path}")

        if dry_run:
            for row in rows:
                data = json.loads(row["data"])
                summary = {k: v for k, v in list(data.items())[:3]}
                print(f"    (dry-run) would insert: {summary} ...")
            totals["copied"] += len(rows)
            continue

        # Ensure target directory and table exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        dst = _connect(target_path)
        _ensure_table(dst)

        if not _target_is_empty(dst):
            existing = dst.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            print(f"    [WARN] target already has {existing} row(s) — skipping to avoid duplicates")
            dst.close()
            totals["skipped"] += len(rows)
            continue

        dst.executemany(
            "INSERT INTO items (data, created_at, updated_at) VALUES (?, ?, ?)",
            [(row["data"], row["created_at"], row["updated_at"]) for row in rows],
        )
        dst.commit()
        dst.close()
        print(f"    [OK] inserted {len(rows)} row(s)")
        totals["copied"] += len(rows)

    src.close()

    print()
    print(f"Migration complete — {totals['copied']} copied, {totals['skipped']} skipped")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without writing anything")
    args = parser.parse_args()

    print(f"Source: {SOURCE_DB}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()
    migrate(dry_run=args.dry_run)
