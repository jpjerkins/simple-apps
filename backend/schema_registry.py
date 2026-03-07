"""Schema loading and validation."""

import json
from pathlib import Path
from typing import Dict, List, Optional

_SCHEMAS_DIR = Path(__file__).parent.parent / "apps"
_schemas: Dict[str, dict] = {}


def _validate_schema(schema: dict, filepath: Path) -> None:
    """Validate that schema has required structure."""
    required_fields = ["id", "name", "fields"]
    for field in required_fields:
        if field not in schema:
            raise ValueError(f"Schema {filepath.name} missing required field: {field}")

    if not isinstance(schema["fields"], list):
        raise ValueError(f"Schema {filepath.name}: 'fields' must be an array")

    for field in schema["fields"]:
        if "id" not in field or "type" not in field:
            raise ValueError(f"Schema {filepath.name}: field missing 'id' or 'type'")


def _load_schemas() -> None:
    """Load all schema files from apps directory."""
    global _schemas
    _schemas = {}

    if not _SCHEMAS_DIR.exists():
        return

    for schema_file in _SCHEMAS_DIR.glob("*.schema.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)

            _validate_schema(schema, schema_file)
            _schemas[schema["id"]] = schema

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading schema {schema_file.name}: {e}")


def get(app_id: str) -> Optional[dict]:
    """Get schema for a specific app."""
    if not _schemas:
        _load_schemas()
    return _schemas.get(app_id)


def get_all() -> List[dict]:
    """Get all loaded schemas."""
    if not _schemas:
        _load_schemas()
    return list(_schemas.values())


def reload() -> None:
    """Reload all schemas from disk."""
    _load_schemas()
