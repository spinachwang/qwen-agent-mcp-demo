"""Configuration loading and validation.

Responsibilities:
- Read .env into os.environ
- Build the LLM config dict that qwen-agent's Assistant expects
- Parse mcp.json and validate its schema
- Expose the system prompt for the assistant

The project root is computed from this file's location, so tests that
call load_mcp_config(tmp_path) get full control over which file is parsed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv as _dotenv_load

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_MCP_CONFIG_PATH: Path = PROJECT_ROOT / "mcp.json"
DEFAULT_ENV_PATH: Path = PROJECT_ROOT / ".env"

REQUIRED_ENV_VARS: tuple[str, ...] = (
    "MINIMAX_API_KEY",
    "MINIMAX_MODEL",
    "MINIMAX_BASE_URL",
)

SYSTEM_PROMPT: str = (
    "You are a helpful assistant with access to a 'notes' MCP tool set "
    "(save_note, read_note, list_notes, delete_note). Use these tools to "
    "remember and recall information across the conversation. Confirm to "
    "the user after every tool call."
)


def load_env(env_path: Path | None = None) -> None:
    """Load environment variables from a .env file. No-op if file is missing.

    Call this BEFORE importing qwen_agent.agents.Assistant so the agent
    picks up env-driven config (e.g. DASHSCOPE_API_KEY) at construction time.
    """
    target = env_path or DEFAULT_ENV_PATH
    if target.exists():
        _dotenv_load(dotenv_path=target)


def build_llm_cfg() -> dict[str, str]:
    """Build the LLM config dict for the qwen-agent Assistant.

    Reads three required env vars (MINIMAX_API_KEY, MINIMAX_MODEL,
    MINIMAX_BASE_URL) and returns a dict shaped for the OpenAI-compatible
    endpoint form. Raises KeyError naming the missing var on any miss.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        # Use the first missing var as the exception key (matches the test)
        raise KeyError(missing[0])
    return {
        "model": os.environ["MINIMAX_MODEL"],
        "model_server": os.environ["MINIMAX_BASE_URL"],
        "api_key": os.environ["MINIMAX_API_KEY"],
    }


def validate_mcp_config(cfg: dict) -> None:
    """Validate the structure of a parsed mcp.json.

    The top-level key MUST be 'mcpServers' (camelCase, plural). qwen-agent's
    MCPManager raises a less clear error if this is wrong; we fail fast here
    with a helpful message.
    """
    if "mcpServers" not in cfg:
        raise ValueError(
            f"Invalid mcp config: top-level key must be 'mcpServers' (got {sorted(cfg.keys())})"
        )


def load_mcp_config(path: Path | None = None) -> dict:
    """Parse mcp.json from disk and validate its schema.

    Raises FileNotFoundError if the file is missing, ValueError if the
    top-level key is wrong, json.JSONDecodeError if the file is not valid JSON.
    """
    target = path or DEFAULT_MCP_CONFIG_PATH
    with open(target, encoding="utf-8") as f:
        cfg = json.load(f)
    validate_mcp_config(cfg)
    return cfg
