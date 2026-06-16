# 05 - 测试计划

> Status: Approved

## 1. 测试层级

| 层级 | 文件位置 | 工具 | mock 策略 |
|---|---|---|---|
| 单元 | `tests/unit/` | pytest | 仅隔离文件系统（tmp_path） |
| 集成 | `tests/integration/` | pytest + mcp SDK | mock LLM；MCP 子进程**真实拉起** |
| 端到端 | 手动 / `scripts/smoke_test.py` | 真实 LLM | 不 mock |

## 2. 测试矩阵

### 2.1 单元测试（`tests/unit/`）

| 文件 | 测试数 | 覆盖目标 |
|---|---|---|
| `test_notes_tools.py` | 5 | `src/notes_store.py` 100% |
| `test_config.py` | 6 | `src/config.py` 100% |

#### `test_notes_tools.py` 用例

| # | 用例 | 断言 |
|---|---|---|
| 1 | `test_save_then_read` | save 后 read 返回相同 content |
| 2 | `test_read_missing` | 不存在的 title 返回 `"not found"` |
| 3 | `test_list_empty` | 空文件返回 `"No notes saved yet."` |
| 4 | `test_list_nonempty` | 多条时返回多行字符串，每个 title 都在 |
| 5 | `test_delete_then_list_empty` | delete 后 list 为空 |

#### `test_config.py` 用例

| # | 用例 | 断言 |
|---|---|---|
| 1 | `test_build_llm_cfg_full_env` | 返回 dict 含 `model`/`model_server`/`api_key` |
| 2 | `test_build_llm_cfg_missing_api_key` | 抛 `KeyError`，消息含 `MINIMAX_API_KEY` |
| 3 | `test_build_llm_cfg_missing_model` | 抛 `KeyError`，消息含 `MINIMAX_MODEL` |
| 4 | `test_load_mcp_config_valid` | 解析成功，返回完整 dict |
| 5 | `test_load_mcp_config_invalid_top_key` | 顶层键是 `mcpservers`（错）抛 `ValueError` |
| 6 | `test_load_mcp_config_missing_file` | 文件不存在抛 `FileNotFoundError` |

### 2.2 集成测试（`tests/integration/`）

| 文件 | 测试数 | 覆盖目标 |
|---|---|---|
| `test_mcp_stdio.py` | 3 | MCP 协议层 + 子进程 |
| `test_assistant_setup.py` | 2 | Assistant 构造 + MCP 接管 |
| `test_webui_launch.py` | 1 | WebUI 启动参数 |

#### `test_mcp_stdio.py` 用例

| # | 用例 | 断言 |
|---|---|---|
| 1 | `test_list_tools_returns_four` | `list_tools()` 返回 4 个工具，名字正确 |
| 2 | `test_call_save_note_writes_file` | `call_tool("save_note", ...)` 后 `data/notes.json` 含正确键值 |
| 3 | `test_call_read_note_after_save` | save 后 read 返回相同 content |

**实现方式**：

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def _exercise_server():
    params = StdioServerParameters(command="python", args=["servers/notes_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools

@pytest.mark.asyncio
async def test_list_tools_returns_four(tmp_path, monkeypatch):
    # 改 cwd 或 env 让 notes_server 写 tmp_path
    ...
    tools = await _exercise_server()
    assert len(tools.tools) == 4
```

#### `test_assistant_setup.py` 用例

| # | 用例 | 断言 |
|---|---|---|
| 1 | `test_mcp_manager_called_with_config` | mock `MCPManager.initConfig`，断言被调 1 次，参数含 `mcpServers` |
| 2 | `test_assistant_constructed_without_error` | 构造 Assistant 不抛异常 |

**mock 策略**：

```python
def test_mcp_manager_called_with_config(monkeypatch):
    init_called = []
    class FakeManager:
        def initConfig(self, cfg): init_called.append(cfg)
    monkeypatch.setattr("qwen_agent.tools.MCPManager", FakeManager)
    bot = Assistant(llm={...}, function_list=[{"mcpServers": {...}}], system_message="x")
    assert len(init_called) == 1
    assert "mcpServers" in init_called[0]
```

#### `test_webui_launch.py` 用例

| # | 用例 | 断言 |
|---|---|---|
| 1 | `test_webui_launch_called` | mock `WebUI`，断言 `.launch()` 被调 1 次 |

**实现**：

```python
def test_webui_launch_called(monkeypatch):
    launch_called = []
    class FakeWebUI:
        def __init__(self, bot): self.bot = bot
        def launch(self, **kw): launch_called.append(kw)
    monkeypatch.setattr("run_web.WebUI", FakeWebUI)
    # 调用 main()
    import run_web
    run_web.main()
    assert len(launch_called) == 1
```

### 2.3 端到端（手动 + smoke 脚本）

**`scripts/smoke_test.py`** — 拉起 `notes_server.py` 子进程，依次：
1. `save_note("smoke", "ok")`
2. `read_note("smoke")` → 期望 `"ok"`
3. 读 `data/notes.json` → 期望 `{"smoke": "ok"}`
4. `delete_note("smoke")`
5. 读 `data/notes.json` → 期望 `{}`

**手动 4 条 Query**（见 [02-specification.md §4.2](./02-specification.md)）。

## 3. 覆盖率目标

| 模块 | 目标 | 实际要求 |
|---|---|---|
| `src/notes_store.py` | 100% | 必须 100% |
| `src/config.py` | 100% | 必须 100% |
| `servers/notes_server.py` | 100% | 必须 100%（仅 4 行包装） |
| `run_web.py` | ≥ 80% | 入口文件，硬约束 |
| **整体** | **≥ 80%** | 硬约束 |

## 4. 运行命令

### 4.1 跑全部测试

```bash
conda run -n qwenagent-mcp python -m pytest --cov=src --cov=servers --cov-report=term-missing
```

### 4.2 只跑单元

```bash
conda run -n qwenagent-mcp python -m pytest tests/unit -v
```

### 4.3 只跑集成

```bash
conda run -n qwenagent-mcp python -m pytest tests/integration -v
```

### 4.4 冒烟测试

```bash
conda run -n qwenagent-mcp python scripts/smoke_test.py
```

## 5. 失败时的处理

| 失败 | 排查方向 |
|---|---|
| `ModuleNotFoundError: qwen_agent` | 跑 `pip install -r requirements.txt` |
| `ModuleNotFoundError: fastmcp` | 同上 |
| `ModuleNotFoundError: pytest` | 跑 `pip install -r requirements-dev.txt` |
| `pytest-asyncio` 警告 | 已在 `pyproject.toml` 配置 `asyncio_mode = "auto"` |
| MCP 子进程超时 | 检查 `servers/notes_server.py` 单独能否启动 |
| 覆盖率不足 | 跑 `pytest --cov-report=html`，看 `htmlcov/index.html` 哪些行没覆盖 |

## 6. CI 建议（可选，未实施）

```yaml
# .github/workflows/test.yml
name: test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: conda-incubator/setup-miniconda@v3
        with:
          environment-file: conda-env.yml
      - run: conda run -n qwenagent-mcp pytest --cov --cov-fail-under=80
```

> Demo 项目暂不实施 CI；本地跑通即满足验收。
