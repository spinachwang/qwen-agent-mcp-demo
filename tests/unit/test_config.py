"""Unit tests for src.config — env loading, LLM config, MCP config parsing."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import (  # RED: these don't exist yet
    build_llm_cfg,
    load_mcp_config,
    validate_mcp_config,
)


# --- build_llm_cfg ---------------------------------------------------------


def test_build_llm_cfg_returns_dict_with_required_keys(monkeypatch):
    """With all env vars set, build_llm_cfg returns a dict with 3 required keys."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")
    cfg = build_llm_cfg()
    assert cfg == {
        "model": "MiniMax-M3",
        "model_server": "https://api.test/v1",
        "api_key": "sk-test",
    }


def test_build_llm_cfg_missing_api_key_raises_keyerror(monkeypatch):
    """If MINIMAX_API_KEY is unset, build_llm_cfg raises KeyError naming the var."""
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")
    with pytest.raises(KeyError) as excinfo:
        build_llm_cfg()
    assert "MINIMAX_API_KEY" in str(excinfo.value)


def test_build_llm_cfg_missing_model_raises_keyerror(monkeypatch):
    """If MINIMAX_MODEL is unset, build_llm_cfg raises KeyError naming the var."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.delenv("MINIMAX_MODEL", raising=False)
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")
    with pytest.raises(KeyError) as excinfo:
        build_llm_cfg()
    assert "MINIMAX_MODEL" in str(excinfo.value)


def test_build_llm_cfg_missing_base_url_raises_keyerror(monkeypatch):
    """If MINIMAX_BASE_URL is unset, build_llm_cfg raises KeyError naming the var."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.delenv("MINIMAX_BASE_URL", raising=False)
    with pytest.raises(KeyError) as excinfo:
        build_llm_cfg()
    assert "MINIMAX_BASE_URL" in str(excinfo.value)


# --- load_mcp_config / validate_mcp_config ---------------------------------


def test_load_mcp_config_parses_valid_json(tmp_path):
    """A well-formed mcp.json with top-level 'mcpServers' is parsed correctly."""
    p = tmp_path / "mcp.json"
    p.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "notes": {"command": "python", "args": ["servers/notes_server.py"]}
                }
            }
        ),
        encoding="utf-8",
    )
    cfg = load_mcp_config(p)
    assert "mcpServers" in cfg
    assert "notes" in cfg["mcpServers"]


def test_load_mcp_config_invalid_top_key_raises_valueerror(tmp_path):
    """A mcp.json whose top-level key is not 'mcpServers' raises ValueError."""
    p = tmp_path / "mcp.json"
    p.write_text(
        json.dumps(
            {
                "mcpservers": {  # lowercase, wrong
                    "notes": {"command": "python", "args": []}
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as excinfo:
        load_mcp_config(p)
    assert "mcpServers" in str(excinfo.value)


def test_load_mcp_config_missing_file_raises_filenotfound(tmp_path):
    """A non-existent mcp.json path raises FileNotFoundError."""
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        load_mcp_config(missing)


def test_validate_mcp_config_accepts_valid_dict():
    """validate_mcp_config returns None (or the config) for a valid dict."""
    cfg = {"mcpServers": {"notes": {"command": "python", "args": []}}}
    # Implementation may return None or the config; just must not raise
    result = validate_mcp_config(cfg)
    assert result is None or result == cfg


def test_validate_mcp_config_rejects_missing_top_key():
    """validate_mcp_config raises ValueError for a dict missing 'mcpServers'."""
    with pytest.raises(ValueError) as excinfo:
        validate_mcp_config({"servers": {}})
    assert "mcpServers" in str(excinfo.value)
