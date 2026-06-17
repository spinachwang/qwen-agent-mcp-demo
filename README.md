# Qwen Agent + MCP Demo

> A minimal demo showing Qwen Agent calling external tools via MCP (Model Context Protocol), built with SDD + TDD.

The project implements a simple **notes** tool suite: `save_note` / `read_note` / `list_notes` / `delete_note`, exposed as an MCP server and consumed by Qwen Agent's built-in Gradio WebUI.

---

## Project status

✅ All 6 TDD task slices complete.
✅ 39 automated tests, 99% line coverage.
✅ WebUI launches end-to-end (verified with `curl`).
✅ Smoke test exercises all 4 MCP tools.

See [docs/specs/04-tasks.md](docs/specs/04-tasks.md) for the task breakdown and [docs/specs/05-test-plan.md](docs/specs/05-test-plan.md) for the test matrix.

---

## Quick start

```bash
# 1. Create the conda env
conda create -n qwenagent-mcp python=3.10 -y

# 2. Install dependencies
conda run -n qwenagent-mcp python -m pip install -r requirements.txt
conda run -n qwenagent-mcp python -m pip install -r requirements-dev.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env and set MINIMAX_API_KEY (and adjust MINIMAX_BASE_URL if needed)

# 4. Run the smoke test (no LLM calls — just MCP round-trip)
conda run -n qwenagent-mcp python scripts/smoke_test.py

# 5. Launch the WebUI
conda run -n qwenagent-mcp python run_web.py
# Open http://127.0.0.1:7860 in your browser
```

---

## Demo queries

Once the WebUI is up, try these in the chat:

| # | Query | Expected tool calls |
|---|---|---|
| 1 | "Save a note titled `meeting` with the content 'Demo with the team at 3pm tomorrow.' Then list all my notes." | `save_note` → `list_notes` |
| 2 | "What did I write in the `meeting` note?" | `read_note` |
| 3 | "Append ' — agenda: MiniMax + qwen-agent + MCP' to the end of the `meeting` note, then read it back to me." | `read_note` → `save_note` → `read_note` |
| 4 | "Delete the `meeting` note and confirm it's gone by listing all notes." | `delete_note` → `list_notes` |

If all four return the expected sequence, the full MCP round-trip is verified.

---

## Architecture

```
┌────────────────────────┐
│   Browser (Gradio)     │  ← qwen_agent.gui.WebUI
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│  qwen_agent Assistant │  ← main LLM loop
└──────────┬─────────────┘
           │ JSON-RPC over stdio
┌──────────▼─────────────┐
│  notes_server.py       │  ← FastMCP server (this repo)
│  4 tools (save/read/   │
│  list/delete_note)     │
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│  src/notes_store.py    │  ← pure-function CRUD
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│  data/notes.json       │
└────────────────────────┘
```

See [docs/specs/03-design.md](docs/specs/03-design.md) for the full architecture and data flow.

---

## Project layout

```
D:\project\demo-qwenagent-mcp\
├── docs/specs/           # SDD: specification-first docs
├── src/                  # config.py, notes_store.py
├── servers/              # notes_server.py (MCP server)
├── tests/                # unit/ + integration/
├── scripts/smoke_test.py # manual end-to-end verification
├── run_web.py            # entry point
├── mcp.json              # MCP server registry
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── conda-env.yml
└── README.md
```

---

## Development

### Workflow

1. Specs first — see `docs/specs/`
2. TDD: write failing test (`test: ...` commit) → minimal impl (`feat: ...` commit) → refactor if needed
3. Code review each commit with the `code-reviewer` subagent
4. Conventional commits (see [docs/specs/01-conventions.md §4.1](docs/specs/01-conventions.md))

### Commands

```bash
# Run all tests with coverage
conda run -n qwenagent-mcp python -m pytest --cov=src --cov=servers --cov=run_web --cov-report=term-missing

# Run only unit tests
conda run -n qwenagent-mcp python -m pytest tests/unit -v

# Run only integration tests
conda run -n qwenagent-mcp python -m pytest tests/integration -v

# End-to-end smoke test
conda run -n qwenagent-mcp python scripts/smoke_test.py
```

### Git safety

Per the project owner's global rules (a destructive-history incident in 2026-05-22):

- ❌ **Never** use `git filter-repo` or `git filter-branch`
- ❌ **Never** use `git push --force` without explicit backup
- ❌ **Never** use `git reset --hard` carelessly
- ✅ Before any history-rewriting operation: `git bundle create backup.bundle --all`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `KeyError: 'MINIMAX_API_KEY'` at startup | `.env` missing or unread | `cp .env.example .env`, then edit |
| HTTP 401/403 from MiniMax | wrong API key or base URL host | re-check `.env` |
| HTTP 404 on `/v1/chat/completions` | base URL missing `/v1` suffix | ensure `MINIMAX_BASE_URL` ends with `/v1` |
| HTTP 400 "model not found" | wrong model name | set `MINIMAX_MODEL=MiniMax-M3` (or whatever the platform exposes) |
| `ValueError: Missing required field "mcpServers"` | `mcp.json` top-level key wrong case | must be exactly `mcpServers` |
| Tools don't appear in UI sidebar | MCP subprocess failed to spawn | verify the Python interpreter is reachable: in `mcp.json`, set `command` to the absolute path of the conda env's Python (e.g. `C:\Users\<user>\miniconda3\envs\qwenagent-mcp\python.exe`) |
| `ImportError: No module named 'fastmcp'` | wrong import path | this project uses `from mcp.server.fastmcp import FastMCP`; the `fastmcp` package is **not** a dependency (avoids a version conflict with `qwen-agent`) |
| `TypeError: issubclass() arg 1 must be a class` at import | `mcp<1.13` shipped with `FastMCP` is incompatible with `from __future__ import annotations` | we deliberately omit the future import in `servers/notes_server.py` so type hints are real class objects; if you add new tools, follow the same pattern |
| `ImportError: No module named 'soundfile'` | `qwen-agent` imports `soundfile` unconditionally at module load | `pip install soundfile` (already in `requirements.txt`; only missing in hand-crafted envs) |
| Install warning `fastmcp-slim X requires pydantic[email]>=2.11.7, but you have pydantic 2.9.2` | `qwen-agent[gui]` pins `pydantic==2.9.2`, conflicting with newer mcp/fastmcp-slim | already mitigated by `mcp>=1.9,<1.13` in `requirements.txt`; do not upgrade mcp beyond 1.12 without also overriding pydantic |
| Port 7860 in use | previous launch left process running | kill stray `python run_web.py`; or pass `server_port=` to `WebUI.run()` |
| Python < 3.10 syntax error | env created with older Python | `conda create -n qwenagent-mcp python=3.10 -y` (recreate) |
| Agent responds but never calls a tool | model is too weak for function calling | MiniMax-M3 is documented as function-calling capable; if it fails, check the platform's docs for a stronger variant |

---

## Specification documents

- [docs/specs/00-index.md](docs/specs/00-index.md) — overview and reading order
- [docs/specs/01-conventions.md](docs/specs/01-conventions.md) — code style, naming, Git commits
- [docs/specs/02-specification.md](docs/specs/02-specification.md) — functional/non-functional requirements, acceptance criteria
- [docs/specs/03-design.md](docs/specs/03-design.md) — architecture, data flow, module APIs
- [docs/specs/04-tasks.md](docs/specs/04-tasks.md) — 6 TDD task slices
- [docs/specs/05-test-plan.md](docs/specs/05-test-plan.md) — test matrix, coverage goals

---

## License

MIT
