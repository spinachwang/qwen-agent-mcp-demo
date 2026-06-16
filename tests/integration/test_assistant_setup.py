"""Integration tests for run_web.build_bot() — Assistant + MCP wiring.

These tests construct an Assistant without ever calling bot.run() and
without spawning real MCP subprocesses. The MCP layer is mocked at the
boundary: we intercept MCPManager().initConfig() to return a list of
fake tool objects, then verify the Agent wired it through to its
function_map.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


class FakeTool:
    """Stand-in for an MCP-discovered tool. Only needs a .name attribute."""

    def __init__(self, name: str) -> None:
        self.name = name


class FakeMCPManager:
    """Captures the initConfig call and returns canned tools.

    The real MCPManager spawns stdio subprocesses and connects to them.
    We bypass that entirely.
    """

    def __init__(self) -> None:
        self.init_calls: list[dict] = []

    def initConfig(self, config: dict) -> list[FakeTool]:
        self.init_calls.append(config)
        return [
            FakeTool("save_note"),
            FakeTool("read_note"),
            FakeTool("list_notes"),
            FakeTool("delete_note"),
        ]


@pytest.fixture
def fake_mcp(monkeypatch):
    """Patch qwen_agent.agent.MCPManager to use a fake singleton."""
    fake = FakeMCPManager()
    monkeypatch.setattr("qwen_agent.agent.MCPManager", lambda: fake)
    return fake


@pytest.fixture
def fake_mcp_module(monkeypatch):
    """Same as fake_mcp but also patches the qwen_agent.tools.MCPManager alias.

    Some versions of qwen-agent import MCPManager via qwen_agent.tools and
    then look it up by name elsewhere. Cover both to be safe.
    """
    fake = FakeMCPManager()
    monkeypatch.setattr("qwen_agent.agent.MCPManager", lambda: fake)
    monkeypatch.setattr("qwen_agent.tools.MCPManager", lambda: fake)
    return fake


def test_build_bot_constructs_assistant_without_error(fake_mcp, monkeypatch):
    """build_bot() returns an Assistant and does not raise."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")

    # Reload run_web so the module picks up the mocked MCPManager.
    for mod in [m for m in list(sys.modules) if m == "run_web"]:
        del sys.modules[mod]
    import run_web

    bot = run_web.build_bot(mcp_config_path=Path("mcp.json"))
    assert bot is not None
    assert hasattr(bot, "run")


def test_build_bot_invokes_mcp_manager_with_mcp_config(fake_mcp, monkeypatch, tmp_path):
    """build_bot() passes the loaded mcp.json to MCPManager().initConfig()."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")

    # Create a real mcp.json for build_bot to read
    mcp_json = tmp_path / "mcp.json"
    mcp_json.write_text(
        '{"mcpServers": {"notes": {"command": "python", "args": ["s.py"]}}}',
        encoding="utf-8",
    )

    for mod in [m for m in list(sys.modules) if m == "run_web"]:
        del sys.modules[mod]
    import run_web

    run_web.build_bot(mcp_config_path=mcp_json)

    assert len(fake_mcp.init_calls) == 1
    cfg = fake_mcp.init_calls[0]
    assert "mcpServers" in cfg
    assert "notes" in cfg["mcpServers"]


def test_build_bot_registers_tools_in_function_map(fake_mcp, monkeypatch, tmp_path):
    """After build_bot, the assistant has 4 tools in its function_map."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")

    mcp_json = tmp_path / "mcp.json"
    mcp_json.write_text(
        '{"mcpServers": {"notes": {"command": "python", "args": ["s.py"]}}}',
        encoding="utf-8",
    )

    for mod in [m for m in list(sys.modules) if m == "run_web"]:
        del sys.modules[mod]
    import run_web

    bot = run_web.build_bot(mcp_config_path=mcp_json)
    assert set(bot.function_map.keys()) == {
        "save_note",
        "read_note",
        "list_notes",
        "delete_note",
    }
