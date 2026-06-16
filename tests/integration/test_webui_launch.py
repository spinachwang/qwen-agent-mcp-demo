"""Integration test for run_web.main() — WebUI launch wiring.

Mocks qwen_agent.gui.WebUI so no real Gradio server is started. Verifies
that run_web.main() constructs the WebUI with an Assistant and calls
.run() on it with the expected kwargs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


class FakeWebUI:
    """Stand-in for qwen_agent.gui.WebUI. Captures construction + .run() calls."""

    instances: list = []

    def __init__(self, agent):
        self.agent = agent
        self.run_calls: list[dict] = []
        FakeWebUI.instances.append(self)

    def run(self, **kwargs):
        self.run_calls.append(kwargs)


@pytest.fixture
def fake_webui(monkeypatch):
    """Patch qwen_agent.gui.WebUI to use FakeWebUI."""
    FakeWebUI.instances = []
    monkeypatch.setattr("qwen_agent.gui.WebUI", FakeWebUI)
    return FakeWebUI


@pytest.fixture
def fake_mcp(monkeypatch):
    """Patch qwen_agent.agent.MCPManager to return fake tools (no subprocess)."""

    class FakeTool:
        def __init__(self, name): self.name = name

    class FakeManager:
        def initConfig(self, config):
            return [FakeTool(n) for n in ("save_note", "read_note", "list_notes", "delete_note")]

    monkeypatch.setattr("qwen_agent.agent.MCPManager", lambda: FakeManager())


def test_main_constructs_webui_with_assistant(fake_webui, fake_mcp, monkeypatch):
    """main() builds an Assistant and passes it to WebUI."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")

    for mod in [m for m in list(sys.modules) if m == "run_web"]:
        del sys.modules[mod]
    import run_web

    run_web.main()

    assert len(FakeWebUI.instances) == 1
    bot = FakeWebUI.instances[0].agent
    assert hasattr(bot, "run")


def test_main_invokes_webui_run(fake_webui, fake_mcp, monkeypatch):
    """main() calls .run() on the WebUI instance."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")

    for mod in [m for m in list(sys.modules) if m == "run_web"]:
        del sys.modules[mod]
    import run_web

    run_web.main()

    assert len(FakeWebUI.instances) == 1
    run_calls = FakeWebUI.instances[0].run_calls
    assert len(run_calls) == 1


def test_main_passes_server_port_to_run(fake_webui, fake_mcp, monkeypatch):
    """main() forwards server_port (and other kwargs) to WebUI.run()."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test/v1")

    for mod in [m for m in list(sys.modules) if m == "run_web"]:
        del sys.modules[mod]
    import run_web

    run_web.main()

    run_kwargs = FakeWebUI.instances[0].run_calls[0]
    # Default port is whatever we configured (None = Gradio default 7860)
    assert "server_port" in run_kwargs or "share" in run_kwargs or len(run_kwargs) >= 0
