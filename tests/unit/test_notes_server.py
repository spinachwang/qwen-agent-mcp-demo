"""Unit tests for servers/notes_server — direct tool invocation.

The 4 @mcp.tool()-decorated functions are thin wrappers that delegate to
src.notes_store. These tests call them directly (bypassing the MCP protocol)
to exercise the server module's lines under the test process's coverage
counter. The protocol-level behavior is covered by tests/integration/test_mcp_stdio.py.

IMPORTANT: We must NOT reload src.notes_store in this file. Other test
modules (e.g. test_notes_tools.py) hold function references to its
module-level globals at import time. Reloading it would orphan those
references and break isolation. Only reload servers.* modules.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def _reload_server_module():
    """Drop cached servers.* modules so the server re-reads NOTES_FILE env var."""
    for mod in [m for m in list(sys.modules) if m.startswith("servers")]:
        del sys.modules[mod]
    return importlib.import_module("servers.notes_server")


@pytest.fixture
def notes_file(tmp_path, monkeypatch):
    """Point the server's NOTES_FILE at a tmp_path file for isolation.

    Uses monkeypatch so env-var and attr changes are auto-undone after the test,
    preventing cross-test pollution.
    """
    target = tmp_path / "notes.json"
    monkeypatch.setattr("src.notes_store.NOTES_FILE", target)
    monkeypatch.setenv("NOTES_FILE", str(target))
    return target


@pytest.fixture
def server(notes_file):
    """Yield a freshly-imported servers.notes_server module bound to notes_file."""
    return _reload_server_module()


def test_save_note_returns_confirmation(server):
    """save_note returns the FR-1 confirmation string."""
    result = server.save_note(title="k", content="v")
    assert result == "Saved note 'k' (1 chars)."


def test_read_note_returns_content_after_save(server):
    """After save_note, read_note returns the stored content."""
    server.save_note(title="k", content="hello")
    assert server.read_note(title="k") == "hello"


def test_read_note_missing_returns_not_found(server):
    """read_note on a missing title returns the 'not found' message."""
    result = server.read_note(title="ghost")
    assert "not found" in result


def test_list_notes_empty_returns_default(server):
    """list_notes on a fresh store returns the default message."""
    result = server.list_notes()
    assert result == "No notes saved yet."


def test_list_notes_nonempty_returns_each(server):
    """list_notes returns one bullet line per saved note."""
    server.save_note(title="a", content="x")
    server.save_note(title="b", content="yy")
    result = server.list_notes()
    assert "- a (1 chars)" in result
    assert "- b (2 chars)" in result


def test_delete_note_removes(server):
    """delete_note removes the note and returns the confirmation."""
    server.save_note(title="temp", content="x")
    result = server.delete_note(title="temp")
    assert result == "Deleted note 'temp'."
    assert "not found" in server.read_note(title="temp")


def test_delete_note_missing_returns_not_found(server):
    """delete_note on a missing title returns the 'not found' message."""
    result = server.delete_note(title="ghost")
    assert "not found" in result