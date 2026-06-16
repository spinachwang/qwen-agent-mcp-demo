"""Unit tests for src.notes_store — pure CRUD on JSON file.

These tests use tmp_path + monkeypatch to isolate filesystem state.
"""
from __future__ import annotations

import pytest

# These imports are intentionally of functions that don't exist yet.
# This is the RED step of TDD — tests must FAIL on first run.
from src.notes_store import (
    delete_one,
    list_all,
    read_one,
    save_one,
)


@pytest.fixture
def notes_file(tmp_path, monkeypatch):
    """Point the module-level NOTES_FILE at a tmp_path file for isolation."""
    target = tmp_path / "notes.json"
    monkeypatch.setattr("src.notes_store.NOTES_FILE", target)
    return target


def test_save_then_read_returns_content(notes_file):
    """Saving a note then reading it returns the same content."""
    msg = save_one("meeting", "3pm tomorrow")
    assert "Saved" in msg
    assert "meeting" in msg
    assert read_one("meeting") == "3pm tomorrow"


def test_read_missing_returns_not_found(notes_file):
    """Reading a title that doesn't exist returns a 'not found' message."""
    assert "not found" in read_one("nonexistent")


def test_list_empty_returns_default_message(notes_file):
    """Listing notes when file is empty/missing returns the default message."""
    assert list_all() == "No notes saved yet."


def test_list_nonempty_returns_all_titles(notes_file):
    """Listing notes returns each title when notes exist."""
    save_one("a", "x")
    save_one("b", "yy")
    out = list_all()
    assert "a" in out
    assert "b" in out
    # Each title with its content length, one per line
    lines = out.strip().splitlines()
    assert len(lines) == 2


def test_delete_removes_note_and_list_is_empty(notes_file):
    """After deleting a note, it can no longer be read and list is empty."""
    save_one("temp", "data")
    assert "Deleted" in delete_one("temp")
    assert "not found" in read_one("temp")
    assert list_all() == "No notes saved yet."


def test_delete_missing_returns_not_found(notes_file):
    """Deleting a title that doesn't exist returns 'not found'."""
    assert "not found" in delete_one("ghost")


def test_save_creates_file_with_correct_format(notes_file):
    """Saving creates the file with the expected JSON structure."""
    save_one("k1", "v1")
    assert notes_file.exists()
    import json
    data = json.loads(notes_file.read_text(encoding="utf-8"))
    assert data == {"k1": "v1"}


def test_corrupt_json_falls_back_to_empty(tmp_path, monkeypatch):
    """If the JSON file is corrupt, load should fall back to an empty dict."""
    target = tmp_path / "notes.json"
    target.write_text("not valid json {{{", encoding="utf-8")
    monkeypatch.setattr("src.notes_store.NOTES_FILE", target)
    # Should not raise; should behave as if empty
    assert list_all() == "No notes saved yet."
    # And saving should overwrite the corrupt file
    save_one("recovered", "ok")
    assert read_one("recovered") == "ok"


def test_non_dict_json_falls_back_to_empty(tmp_path, monkeypatch):
    """If the JSON file contains a non-dict (e.g. a list), load returns {}."""
    target = tmp_path / "notes.json"
    target.write_text("[1, 2, 3]", encoding="utf-8")
    monkeypatch.setattr("src.notes_store.NOTES_FILE", target)
    assert list_all() == "No notes saved yet."
