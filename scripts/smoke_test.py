"""End-to-end smoke test: spawn the notes MCP server, exercise the 4 tools, verify.

This script is meant to be run manually after a fresh install to confirm
the full MCP stack works:

    conda run -n qwenagent-mcp python scripts/smoke_test.py

It writes to a tmp file (NOTES_FILE in env) so the real data/notes.json
is never touched. Exits 0 on success, non-zero on any failure.
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Ensure project root is on path so 'servers' is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SERVER_PATH = PROJECT_ROOT / "servers" / "notes_server.py"


def _b(s: str) -> str:
    """Extract the text payload from the first content block of a tool result."""
    return s.content[0].text


async def _run_smoke() -> int:
    # Use a tmp file for the smoke test so we don't pollute data/notes.json
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    tmp.close()
    notes_file = Path(tmp.name)
    notes_file.unlink()  # start from a missing-file state

    env = {**os.environ, "NOTES_FILE": str(notes_file)}
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER_PATH)], env=env
    )

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 1. list_tools returns 4
                tools = await session.list_tools()
                names = sorted(t.name for t in tools.tools)
                assert names == ["delete_note", "list_notes", "read_note", "save_note"], (
                    f"unexpected tools: {names}"
                )
                print(f"  [OK] list_tools → {names}")

                # 2. save_note
                r = await session.call_tool(
                    "save_note", {"title": "smoke", "content": "hello-mcp"}
                )
                assert "Saved" in _b(r), f"unexpected save_note response: {_b(r)}"
                assert notes_file.exists(), "notes file not created"
                print(f"  [OK] save_note → {_b(r)!r}, file created")

                # 3. read_note (fresh session to prove persistence across processes is unnecessary;
                #    the in-process state is fine for smoke)
                r = await session.call_tool("read_note", {"title": "smoke"})
                assert _b(r) == "hello-mcp", f"unexpected read_note response: {_b(r)!r}"
                print(f"  [OK] read_note → {_b(r)!r}")

                # 4. list_notes
                r = await session.call_tool("list_notes", {})
                assert "smoke" in _b(r), f"unexpected list_notes response: {_b(r)!r}"
                print(f"  [OK] list_notes → {_b(r)!r}")

                # 5. delete_note
                r = await session.call_tool("delete_note", {"title": "smoke"})
                assert "Deleted" in _b(r), f"unexpected delete_note response: {_b(r)!r}"
                print(f"  [OK] delete_note → {_b(r)!r}")

                # 6. read_note on deleted → not found
                r = await session.call_tool("read_note", {"title": "smoke"})
                assert "not found" in _b(r), f"unexpected read-after-delete: {_b(r)!r}"
                print(f"  [OK] read_note after delete → {_b(r)!r}")
    finally:
        if notes_file.exists():
            notes_file.unlink()

    return 0


def main() -> int:
    print("Smoke test: notes MCP server end-to-end")
    print(f"  server: {SERVER_PATH}")
    try:
        return asyncio.run(_run_smoke())
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        return 1
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
