# 03 - 架构设计

> Status: Approved

## 1. 系统组件图

```
┌────────────────────────────────────────────────────────────┐
│                       Browser (User)                        │
└──────────────────────────┬─────────────────────────────────┘
                           │ HTTP (Gradio)
┌──────────────────────────▼─────────────────────────────────┐
│   qwen_agent.gui.WebUI  (Gradio 5)                         │
│   - 聊天输入框 + 工具侧栏 + 文件上传                         │
└──────────────────────────┬─────────────────────────────────┘
                           │ 同步
┌──────────────────────────▼─────────────────────────────────┐
│   qwen_agent.agents.Assistant                              │
│   - 维护消息历史                                            │
│   - 调用 LLM，解析 tool_call                                │
│   - 委托 MCPManager 调工具                                  │
└──────────┬─────────────────────────┬───────────────────────┘
           │ HTTP                    │ JSON-RPC over stdio
           │ /v1/chat/completions     │
┌──────────▼─────────┐    ┌──────────▼───────────────────────┐
│  MiniMax API       │    │  qwen_agent.tools.MCPManager     │
│  (OpenAI-compat)   │    │  - 读 mcp.json                    │
│  model: M3         │    │  - spawn  stdio 子进程            │
└────────────────────┘    │  - 工具发现 / 协议层              │
                          └──────────┬───────────────────────┘
                                     │ JSON-RPC over stdio
                          ┌──────────▼───────────────────────┐
                          │  servers/notes_server.py          │
                          │  FastMCP("notes-server")         │
                          │  - 4 tools                        │
                          │  - 委托 src.notes_store            │
                          └──────────┬───────────────────────┘
                                     │
                          ┌──────────▼───────────────────────┐
                          │  src/notes_store.py               │
                          │  - load_all / save_all            │
                          │  - read_one / list_all / delete   │
                          └──────────┬───────────────────────┘
                                     │ 读 / 写
                          ┌──────────▼───────────────────────┐
                          │  data/notes.json                  │
                          └──────────────────────────────────┘
```

## 2. 数据流（一次工具调用）

```
User → "Save a note titled 'meeting' with content '3pm'."

1. WebUI 接收输入
2. Assistant 拼 prompt: system + tools schema + history + user msg
3. POST /v1/chat/completions → MiniMax M3
4. MiniMax 返回 tool_call: {name: "notes.save_note", args: {title, content}}
5. Assistant 解析 tool_call, 委托 MCPManager
6. MCPManager 通过 stdio 发 JSON-RPC 给 notes_server.py 子进程
7. 子进程 FastMCP 路由到 save_note 函数
8. save_note 调用 src.notes_store.save_one
9. notes_store 写 data/notes.json
10. 返回 "Saved note 'meeting' (3 chars)."
11. 子进程 JSON-RPC 回 MCPManager
12. MCPManager 封装为 tool result 喂回 Assistant
13. Assistant 再次调用 LLM（带 tool result）
14. MiniMax 返回自然语言总结
15. 流式 chunk 推回 WebUI 渲染
```

## 3. 模块划分

### 3.1 `src/notes_store.py`（纯函数层）

**职责**：4 个 CRUD 操作的纯逻辑，不依赖 fastmcp / qwen_agent / MCP。

**公开 API**：

```python
NOTES_FILE: Path  # 模块级常量，由测试 monkeypatch 注入

def _load() -> dict[str, str]: ...
def _save(notes: dict[str, str]) -> None: ...
def save_one(title: str, content: str) -> str: ...
def read_one(title: str) -> str: ...
def list_all() -> str: ...
def delete_one(title: str) -> str: ...
```

**关键不变量**：
- 函数无副作用的输入；输出字符串符合 FR-1
- JSON 损坏 → `_load()` 返回 `{}`（不抛错）
- 文件不存在 → `_load()` 返回 `{}`

### 3.2 `servers/notes_server.py`（FastMCP 适配层）

**职责**：把 `notes_store` 的纯函数暴露为 MCP 工具。

**结构**：

```python
mcp = FastMCP("notes-server")

@mcp.tool()
def save_note(title: str, content: str) -> str: ...
# 其它 3 个类似

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**约束**：
- 4 个 `@mcp.tool()` 名字与 `notes_store` 的 4 个函数一一对应
- 4 个 docstring 必须描述清楚（LLLM 靠它决定何时调用）
- 4 个函数只做**薄包装**——一行 return，不夹业务逻辑

### 3.3 `src/config.py`（配置层）

**职责**：env 加载、LLM 配置构造、MCP 配置加载、系统提示词。

**公开 API**：

```python
PROJECT_ROOT: Path

def load_env(env_path: Path | None = None) -> None: ...
def build_llm_cfg() -> dict: ...
def load_mcp_config(path: Path | None = None) -> dict: ...
def validate_mcp_config(cfg: dict) -> None: ...  # 抛 ValueError if 缺 mcpServers 键

SYSTEM_PROMPT: str
```

### 3.4 `run_web.py`（入口）

**职责**：串联配置、构造 Assistant、启动 WebUI。

**关键顺序**：
1. `load_env()` 必须在 `from qwen_agent.agents import Assistant` **之前**
2. 构造 `Assistant(llm=..., function_list=[mcp_cfg], system_message=...)`
3. `WebUI(bot).launch()`

### 3.5 `mcp.json`（声明式配置）

```json
{
  "mcpServers": {
    "notes": {
      "command": "python",
      "args": ["servers/notes_server.py"]
    }
  }
}
```

> 顶层键 `mcpServers` 强校验（缺则 `MCPManager` 抛 `ValueError`）。

## 4. 关键技术决策

| 决策 | 备选 | 选择理由 |
|---|---|---|
| 存储用 JSON 文件 | SQLite / in-memory | 可直接 `cat` 验证，< 200 行 |
| 4 个工具拆成 store + server 两层 | server 内联实现 | 纯函数易测，符合 TDD |
| `function_list=[mcp_cfg]` 形式 | `mcp_servers=` 关键字 | qwen-agent 文档示例更直接 |
| 用 `model_server` + `api_key` 显式形式 | `model_type="openai"` | host 可视、不被默认值干扰 |
| 集成测试用真实 stdio | 全部 mock | mock MCP 协议层失去测试意义 |
| LLM 集成测试用 mock | 真实 API | CI 不依赖网络、密钥、可重放 |

## 5. 错误处理矩阵

| 错误 | 抛出位置 | 用户可见 |
|---|---|---|
| `.env` 缺 `MINIMAX_API_KEY` | `build_llm_cfg` | 启动崩溃 + 明确消息 |
| `mcp.json` 缺 `mcpServers` | `validate_mcp_config` | 启动崩溃 + 提示正确键名 |
| MCP 子进程启动失败 | `MCPManager` | UI 侧栏缺工具 + 控制台 traceback |
| 笔记 JSON 损坏 | `_load` | 静默回退到空字典 + 写入时覆盖 |
| 工具调用参数错误 | FastMCP | 工具返回 `"Invalid input: ..."` |

## 6. 部署与运行

无部署——本地开发即运行。详见 [04-tasks.md](./04-tasks.md) 与 [05-test-plan.md](./05-test-plan.md)。
