"""Entry point: launch the qwen-agent built-in Gradio WebUI.

This module wires together env loading, LLM config, MCP config, and the
qwen-agent Assistant. The TDD slice for the WebUI launch is in T5; this
file is finalized in that commit.

Run with:
    conda run -n qwenagent-mcp python run_web.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# CRITICAL: load_env() must run BEFORE we import qwen_agent.agents.Assistant,
# so any env-driven agent config (e.g. DASHSCOPE_API_KEY) is visible.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.config import (  # noqa: E402  (path adjusted above)
    PROJECT_ROOT,
    SYSTEM_PROMPT,
    build_llm_cfg,
    load_env,
    load_mcp_config,
)

load_env()


def build_bot(
    llm_cfg: dict | None = None,
    mcp_config_path: Path | None = None,
    system_prompt: str = SYSTEM_PROMPT,
):
    """Construct the qwen-agent Assistant wired to the LLM and the MCP server.

    Args:
        llm_cfg: Optional pre-built LLM config dict. If None, build_llm_cfg()
                 is called to read from environment.
        mcp_config_path: Optional path to mcp.json. If None, the project-root
                         mcp.json is used.
        system_prompt: System message for the assistant.

    Returns:
        A qwen_agent.agents.Assistant instance ready to be passed to
        qwen_agent.gui.WebUI(...).
    """
    from qwen_agent.agents import Assistant  # imported here, after load_env

    if llm_cfg is None:
        llm_cfg = build_llm_cfg()
    if mcp_config_path is None:
        mcp_config_path = PROJECT_ROOT / "mcp.json"
    mcp_cfg = load_mcp_config(mcp_config_path)

    bot = Assistant(
        llm=llm_cfg,
        function_list=[mcp_cfg],  # MCPManager auto-detects the 'mcpServers' key
        system_message=system_prompt,
    )
    return bot


def main() -> None:
    """Launch the qwen-agent built-in Gradio WebUI."""
    from qwen_agent.gui import WebUI

    bot = build_bot()
    # qwen-agent's WebUI uses .run() to start the Gradio server.
    # Default server_port=None lets Gradio pick (typically 7860).
    WebUI(bot).run()


if __name__ == "__main__":  # pragma: no cover
    main()
