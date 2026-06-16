"""Entry point: launch the qwen-agent built-in Gradio WebUI.

Full implementation arrives in T4+T5 commits. Currently a stub.
"""
from __future__ import annotations


def main() -> None:  # pragma: no cover
    """Wire env loading, Assistant construction, and WebUI launch.

    Implementation order (see docs/specs/04-tasks.md):
    - T4: construct Assistant with MCP config and system prompt
    - T5: launch WebUI
    """
    raise NotImplementedError(
        "run_web.main() will be implemented in T4 + T5 — see docs/specs/04-tasks.md"
    )


if __name__ == "__main__":  # pragma: no cover
    main()
