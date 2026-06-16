"""Notes MCP server — exposes src.notes_store as 4 MCP tools over stdio.

The server is a thin adapter: each @mcp.tool() function delegates to a
corresponding function in src.notes_store. No business logic here.

Environment variables:
    NOTES_FILE: optional override for the storage path. If unset, defaults
                to <project_root>/data/notes.json. Tests set this to a
                tmp_path to isolate from real data.

Run standalone (for debugging):
    NOTES_FILE=/tmp/debug.json python servers/notes_server.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Make src/ importable when this file is run as `python servers/notes_server.py`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.notes_store import (  # noqa: E402  (path adjusted above)
    delete_one,
    list_all,
    read_one,
    save_one,
)

# Allow tests (and ad-hoc runs) to redirect storage via env var
_NOTES_FILE_ENV = os.environ.get("NOTES_FILE")
if _NOTES_FILE_ENV:
    import src.notes_store as _store

    _store.NOTES_FILE = Path(_NOTES_FILE_ENV)

mcp = FastMCP("notes-server")


@mcp.tool()
def save_note(title: str, content: str) -> str:
    """Save (or overwrite) a note. Returns a confirmation string.

    Use this when the user wants to remember a piece of information under a
    short, memorable title. Overwrites silently if the title already exists.
    """
    return save_one(title, content)


@mcp.tool()
def read_note(title: str) -> str:
    """Read a single note by its exact title.

    Returns the stored content, or a 'not found' message if no note exists
    with that title.
    """
    return read_one(title)


@mcp.tool()
def list_notes() -> str:
    """List all saved note titles with their content lengths.

    Returns one bullet line per note, or a 'No notes saved yet.' message
    when the store is empty.
    """
    return list_all()


@mcp.tool()
def delete_note(title: str) -> str:
    """Delete a note by its exact title.

    Returns a confirmation string on success, or a 'not found' message
    if no note exists with that title.
    """
    return delete_one(title)


if __name__ == "__main__":
    # stdio transport — qwen-agent's MCPManager spawns us this way.
    mcp.run(transport="stdio")
