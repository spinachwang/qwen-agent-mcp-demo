# Qwen Agent + MCP Demo

> A minimal demo showing Qwen Agent calling external tools via MCP (Model Context Protocol).

**Status**: 🚧 in development (Phase 2/3 of SDD plan)

## Quick links

- 📋 [Specification docs](docs/specs/00-index.md) — start here
- 🏃 [Run instructions](#running) — how to launch the demo
- 🐛 [Troubleshooting](#troubleshooting) — common failures

## What this project does

```
User → Browser (Gradio WebUI)
     → Qwen Agent Assistant
     → MCP Manager
     → stdio subprocess (notes_server.py)
     → JSON file
```

See [docs/specs/03-design.md](docs/specs/03-design.md) for the full architecture.

## Running

```bash
# 1. Create conda env
conda create -n qwenagent-mcp python=3.10 -y
conda run -n qwenagent-mcp python -m pip install -r requirements.txt
conda run -n qwenagent-mcp python -m pip install -r requirements-dev.txt

# 2. Configure
cp .env.example .env
# Edit .env to set MINIMAX_API_KEY

# 3. Run
conda run -n qwenagent-mcp python run_web.py
# Open http://127.0.0.1:7860
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `KeyError: 'MINIMAX_API_KEY'` | Copy `.env.example` to `.env` and fill in the key |
| `ValueError: Missing required field "mcpServers"` | Check `mcp.json` top-level key is exactly `mcpServers` |
| Port 7860 in use | Pass `server_port=7861` to `WebUI.launch()` |
| Python <3.10 syntax error | Recreate env with Python 3.10 |
| Agent doesn't call tools | Confirm `system_message` is passed; check LLM model supports function calling |

For more, see [docs/specs/02-specification.md](docs/specs/02-specification.md) §6 (risks).

## Development

- Specification-first: see `docs/specs/`
- TDD workflow: tests before code
- Conventional commits (see [01-conventions.md §4.1](docs/specs/01-conventions.md))

```bash
# Run tests
conda run -n qwenagent-mcp python -m pytest --cov

# Run smoke test
conda run -n qwenagent-mcp python scripts/smoke_test.py
```
