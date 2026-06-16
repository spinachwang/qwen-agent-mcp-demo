"""Pure-function CRUD on a JSON file. No MCP, no async, easy to unit-test.

This module is the single source of truth for note persistence. The FastMCP
server in servers/notes_server.py is a thin adapter that exposes these
functions as MCP tools.

Design:
- NOTES_FILE is a module-level Path; tests monkeypatch it for isolation.
- All public functions return user-facing strings matching FR-1 in
  docs/specs/02-specification.md.
- JSON corruption falls back to an empty dict (does not raise).
"""
from __future__ import annotations

import json
from pathlib import Path

# Default location: <project_root>/data/notes.json
# Tests override via monkeypatch.setattr("src.notes_store.NOTES_FILE", tmp_path/...).
_DEFAULT_FILE: Path = Path(__file__).resolve().parent.parent / "data" / "notes.json"
NOTES_FILE: Path = _DEFAULT_FILE


def _load() -> dict[str, str]:
    """Load all notes from disk. Returns {} if file is missing or corrupt."""
    if not NOTES_FILE.exists():
        return {}
    try:
        data = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _save(notes: dict[str, str]) -> None:
    """Persist all notes to disk. Creates parent directories as needed."""
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(
        json.dumps(notes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_one(title: str, content: str) -> str:
    """Save (or overwrite) a single note. Returns a confirmation message."""
    notes = _load()
    notes[title] = content
    _save(notes)
    return f"Saved note '{title}' ({len(content)} chars)."


def read_one(title: str) -> str:
    """Read a single note by exact title. Returns 'not found' if missing."""
    notes = _load()
    if title not in notes:
        return f"Note '{title}' not found."
    return notes[title]


def list_all() -> str:
    """List all note titles with their content lengths.

    Returns the default 'No notes saved yet.' message when empty.
    """
    notes = _load()
    if not notes:
        return "No notes saved yet."
    return "\n".join(f"- {t} ({len(c)} chars)" for t, c in notes.items())


def delete_one(title: str) -> str:
    """Delete a single note by exact title. Returns 'not found' if missing."""
    notes = _load()
    if title not in notes:
        return f"Note '{title}' not found."
    del notes[title]
    _save(notes)
    return f"Deleted note '{title}'."
