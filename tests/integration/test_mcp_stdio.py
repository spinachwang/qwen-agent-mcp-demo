"""Integration tests for the notes MCP server (servers/notes_server.py).

These tests spawn the server as a real subprocess via stdio_client — they do
NOT mock the MCP protocol layer. The server is expected to read NOTES_FILE
from the environment to know where to persist notes (so tests can isolate
the file to a tmp_path).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to the server module — same dir as this test's parent
SERVER_PATH = Path(__file__).resolve().parent.parent.parent / "servers" / "notes_server.py"


def _server_params(notes_file: Path) -> StdioServerParameters:
    """Build stdio params that point NOTES_FILE at the given tmp path."""
    return StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env={**os.environ, "NOTES_FILE": str(notes_file)},
    )


async def _exercise_server(notes_file: Path, action):
    """Spawn the server and run a coroutine that uses the session."""
    params = _server_params(notes_file)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await action(session)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tools_returns_four(tmp_path):
    """list_tools() should return exactly 4 tools: save_note/read_note/list_notes/delete_note."""
    notes_file = tmp_path / "notes.json"

    async def action(session: ClientSession):
        result = await session.list_tools()
        return result.tools

    tools = await _exercise_server(notes_file, action)
    names = sorted(t.name for t in tools)
    assert names == ["delete_note", "list_notes", "read_note", "save_note"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_note_writes_file(tmp_path):
    """call_tool('save_note', ...) should persist the note to NOTES_FILE on disk."""
    notes_file = tmp_path / "notes.json"

    async def action(session: ClientSession):
        return await session.call_tool(
            "save_note", {"title": "k1", "content": "v1"}
        )

    result = await _exercise_server(notes_file, action)
    # Result has at least one content block; first one is text
    text = result.content[0].text
    assert "Saved" in text and "k1" in text

    # Side effect: file is created with the expected JSON
    assert notes_file.exists()
    data = json.loads(notes_file.read_text(encoding="utf-8"))
    assert data == {"k1": "v1"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_then_read_note_roundtrip(tmp_path):
    """Save a note, then read it back via the MCP server in a fresh session."""
    notes_file = tmp_path / "notes.json"

    # First session: save
    async def save_action(session: ClientSession):
        return await session.call_tool(
            "save_note", {"title": "meeting", "content": "3pm"}
        )

    await _exercise_server(notes_file, save_action)

    # Second session: read
    async def read_action(session: ClientSession):
        return await session.call_tool("read_note", {"title": "meeting"})

    result = await _exercise_server(notes_file, read_action)
    text = result.content[0].text
    assert text == "3pm"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_notes_empty_returns_default(tmp_path):
    """list_notes() on a fresh store returns the default empty message."""
    notes_file = tmp_path / "notes.json"

    async def action(session: ClientSession):
        return await session.call_tool("list_notes", {})

    result = await _exercise_server(notes_file, action)
    text = result.content[0].text
    assert "No notes saved yet" in text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_note_removes_from_file(tmp_path):
    """delete_note() removes the key from the underlying JSON file."""
    notes_file = tmp_path / "notes.json"
    # Pre-populate
    notes_file.write_text(json.dumps({"temp": "x"}), encoding="utf-8")

    async def action(session: ClientSession):
        return await session.call_tool("delete_note", {"title": "temp"})

    await _exercise_server(notes_file, action)

    data = json.loads(notes_file.read_text(encoding="utf-8"))
    assert data == {}
