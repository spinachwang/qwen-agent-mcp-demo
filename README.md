# Qwen Agent + MCP Demo

> 一个最小可运行的 Demo：Qwen Agent 通过 MCP（Model Context Protocol）调用外部工具，使用 **SDD + TDD** 开发。

项目实现了一套简单的**笔记**工具：`save_note` / `read_note` / `list_notes` / `delete_note`，由一个自定义 MCP 服务暴露给 Qwen Agent 自带的 Gradio WebUI 使用。

---

## 项目状态

- ✅ 6 个 TDD 任务切片全部完成
- ✅ **39 个自动化测试**，**99% 行覆盖率**
- ✅ WebUI 端到端启动验证通过（`curl` 命中 7860 端口）
- ✅ 冒烟测试覆盖全部 4 个 MCP 工具
- ✅ 16 个原子 Git 提交（按 conventional commits 组织）

详细任务分解见 [docs/specs/04-tasks.md](docs/specs/04-tasks.md)，测试矩阵见 [docs/specs/05-test-plan.md](docs/specs/05-test-plan.md)。

---

## 快速开始

```bash
# 1. 创建 conda 环境
conda create -n qwenagent-mcp python=3.10 -y

# 2. 安装依赖
conda run -n qwenagent-mcp python -m pip install -r requirements.txt
conda run -n qwenagent-mcp python -m pip install -r requirements-dev.txt

# 3. 配置凭据
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY（必要时调整 MINIMAX_BASE_URL）

# 4. 跑冒烟测试（不调用 LLM，仅验证 MCP 全链路）
conda run -n qwenagent-mcp python scripts/smoke_test.py

# 5. 启动 WebUI
conda run -n qwenagent-mcp python run_web.py
# 浏览器打开 http://127.0.0.1:7860
```

---

## 演示 Query

WebUI 起来后，在聊天框里试试这几句（中文或英文都行）：

| # | Query | 期望工具调用序列 |
|---|---|---|
| 1 | 「保存一个笔记叫 `meeting`，内容是『明天下午 3 点跟团队 demo』。然后列出我所有笔记。」 | `save_note` → `list_notes` |
| 2 | 「我刚才在 `meeting` 笔记里写了什么？」 | `read_note` |
| 3 | 「在 `meeting` 笔记末尾追加『—— 议程：MiniMax + qwen-agent + MCP』，然后再读给我听一遍。」 | `read_note` → `save_note` → `read_note` |
| 4 | 「删除 `meeting` 笔记，再列一次确认没了。」 | `delete_note` → `list_notes` |

四条全部按预期序列返回 → MCP 全链路验证通过。

---

## 架构

```
┌────────────────────────┐
│   Browser (Gradio)     │  ← qwen_agent.gui.WebUI
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│  qwen_agent Assistant │  ← 主 LLM 循环
└──────────┬─────────────┘
           │ JSON-RPC over stdio
┌──────────▼─────────────┐
│  notes_server.py       │  ← FastMCP 服务（本仓库）
│  4 个工具              │
│  (save/read/list/del)  │
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│  src/notes_store.py    │  ← 纯函数 CRUD
└──────────┬─────────────┘
           │
┌──────────▼─────────────┐
│  data/notes.json       │
└────────────────────────┘
```

完整架构与数据流见 [docs/specs/03-design.md](docs/specs/03-design.md)。

---

## 目录结构

```
D:\project\demo-qwenagent-mcp\
├── docs/specs/           # SDD：规范文档
├── src/                  # config.py, notes_store.py
├── servers/              # notes_server.py（MCP 服务）
├── tests/                # unit/ + integration/
├── scripts/smoke_test.py # 手动端到端冒烟测试
├── run_web.py            # 入口
├── mcp.json              # MCP 服务注册
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── conda-env.yml
└── README.md
```

---

## 开发

### 工作流

1. 规范先行 — 见 `docs/specs/`
2. TDD：先写失败测试（`test: ...` commit）→ 最小实现（`feat: ...` commit）→ 必要时重构
3. 每个 commit 用 `code-reviewer` 子代理审查
4. Conventional Commits 格式（见 [docs/specs/01-conventions.md §4.1](docs/specs/01-conventions.md)）

### 常用命令

```bash
# 跑全部测试 + 覆盖率
conda run -n qwenagent-mcp python -m pytest --cov=src --cov=servers --cov=run_web --cov-report=term-missing

# 只跑单元测试
conda run -n qwenagent-mcp python -m pytest tests/unit -v

# 只跑集成测试
conda run -n qwenagent-mcp python -m pytest tests/integration -v

# 端到端冒烟
conda run -n qwenagent-mcp python scripts/smoke_test.py
```

### Git 安全

按项目所有者全局规则（2026-05-22 有过一次破坏性历史事故）：

- ❌ **禁止** `git filter-repo` / `git filter-branch`
- ❌ **禁止** `git push --force`（除非明确知道有远程备份）
- ❌ **禁止** 随意 `git reset --hard`
- ✅ 任何重写历史前先 `git bundle create backup.bundle --all`

---

## 故障排查

| 现象 | 原因 | 修复 |
|---|---|---|
| 启动报 `KeyError: 'MINIMAX_API_KEY'` | `.env` 缺失或读不到 | `cp .env.example .env` 后编辑填入 key |
| MiniMax 返回 HTTP 401/403 | API Key 错或 base URL 错 | 核对 `.env` 里的 key 和 host |
| HTTP 404 `/v1/chat/completions` | base URL 没以 `/v1` 结尾 | qwen-agent 会自动追加 `/chat/completions`，base 必须含 `/v1` |
| HTTP 400 "model not found" | 模型名错 | 设 `MINIMAX_MODEL=MiniMax-M3`（或 MiniMax 平台实际暴露的名字）|
| `ValueError: Missing required field "mcpServers"` | `mcp.json` 顶层键大小写错 | 必须严格是 `mcpServers`（camelCase、复数 s） |
| UI 侧栏看不到任何工具 | MCP 子进程拉起失败 | 在 `mcp.json` 把 `command` 改成 conda 环境 python 的绝对路径（例：`C:\Users\<user>\miniconda3\envs\qwenagent-mcp\python.exe`） |
| `ImportError: No module named 'fastmcp'` | 导入路径错 | 本项目用 `from mcp.server.fastmcp import FastMCP`；`fastmcp` 包**不**是依赖（避免与 `qwen-agent` 版本冲突） |
| `TypeError: issubclass() arg 1 must be a class` 出现在 import 时 | mcp 1.9–1.12 自带的 `FastMCP` 不兼容 `from __future__ import annotations` | `servers/notes_server.py` 故意省略 future import，保证注解是真实 class 对象；新增工具时遵循同一约定 |
| `ImportError: No module named 'soundfile'` | `qwen-agent` 在模块加载时无条件 import `soundfile` | `pip install soundfile`（已在 `requirements.txt`；手搓环境才会缺）|
| 安装报 `fastmcp-slim X requires pydantic[email]>=2.11.7, but you have pydantic 2.9.2` | `qwen-agent[gui]` 把 pydantic 钉在 2.9.2，与新 mcp/fastmcp-slim 冲突 | 已在 `requirements.txt` 中限定 `mcp>=1.9,<1.13`；不要在没同时升 pydantic 的情况下升 mcp 超过 1.12 |
| 端口 7860 被占 | 上一次进程没退出 | 杀掉残留 `python run_web.py`；或在 `WebUI.run()` 传 `server_port=` 改端口 |
| Python < 3.10 语法错 | 环境用的旧 Python | `conda create -n qwenagent-mcp python=3.10 -y`（重建） |
| Agent 回答了但从不调工具 | 模型 function-calling 能力太弱 | MiniMax-M3 文档支持 function calling；如失败，去 MiniMax 平台文档找更强的变体 |

---

## 规范文档

- [docs/specs/00-index.md](docs/specs/00-index.md) — 总览和阅读顺序
- [docs/specs/01-conventions.md](docs/specs/01-conventions.md) — 代码风格、命名、Git 提交格式
- [docs/specs/02-specification.md](docs/specs/02-specification.md) — 功能/非功能需求、验收标准
- [docs/specs/03-design.md](docs/specs/03-design.md) — 架构、数据流、模块 API
- [docs/specs/04-tasks.md](docs/specs/04-tasks.md) — 6 个 TDD 任务切片
- [docs/specs/05-test-plan.md](docs/specs/05-test-plan.md) — 测试矩阵、覆盖率目标

---

## 许可证

MIT
