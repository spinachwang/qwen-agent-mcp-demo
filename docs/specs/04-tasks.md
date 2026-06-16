# 04 - 任务分解

> Status: Approved
> 实施方式: 6 个 TDD 任务切片（RED → GREEN → IMPROVE → review → commit）

## 总览

| ID | 切片 | 预期 commit 数 | 依赖 |
|---|---|---|---|
| T1 | notes 纯函数 | 2 (test + feat) | 无 |
| T2 | FastMCP 适配层 | 2 (test + feat) | T1 |
| T3 | config 模块 | 2 (test + feat) | 无（独立） |
| T4 | Assistant 构造 | 2 (test + feat) | T2, T3 |
| T5 | WebUI 启动 | 2 (test + feat) | T4 |
| T6 | README + 冒烟脚本 | 1 (docs) | T5 |

加上前置 2 个 commit（docs + chore），共 **12+ commits**。

---

## T1: notes 纯函数

**目标文件**：`src/notes_store.py`, `tests/unit/test_notes_tools.py`

**RED 步骤**

1. 创建 `tests/unit/test_notes_tools.py`，5 个测试：
   - `test_save_then_read_returns_content`
   - `test_read_missing_returns_not_found`
   - `test_list_empty_returns_default_message`
   - `test_list_nonempty_returns_all_titles`
   - `test_delete_removes_note_and_list_is_empty`
2. 每个测试用 `tmp_path` + `monkeypatch` 隔离 `NOTES_FILE`
3. 跑 `pytest tests/unit/test_notes_tools.py` → **全部失败**（`ModuleNotFoundError`）
4. `git add . && git commit -m "test: add failing tests for notes CRUD on JSON file"`

**GREEN 步骤**

1. 创建 `src/__init__.py`（空）
2. 创建 `src/notes_store.py`：
   - 模块级 `NOTES_FILE: Path = Path(__file__).resolve().parent.parent / "data" / "notes.json"`
   - `_load() / _save() / save_one() / read_one() / list_all() / delete_one()`
3. 跑 `pytest` → **5 个测试全过**
4. 跑 `pytest --cov=src/notes_store --cov-report=term-missing` → **覆盖率 100%**
5. `git add . && git commit -m "feat: implement notes CRUD store against JSON file"`

**IMPROVE 步骤**（按 code review 反馈决定）

- 可能方向：路径解析提取为可注入参数；类型注解补全；docstring 完整

**验收**：
- [ ] 5 个测试全过
- [ ] 覆盖率 100%
- [ ] `code-reviewer` 子代理通过

---

## T2: FastMCP 适配层

**目标文件**：`servers/notes_server.py`, `tests/integration/test_mcp_stdio.py`, `servers/__init__.py`

**RED 步骤**

1. 创建 `servers/__init__.py`（空）
2. 创建 `tests/integration/test_mcp_stdio.py`：
   - 用 `mcp.client.stdio.stdio_client` + `ClientSession` 拉起 `servers/notes_server.py` 子进程
   - 测试 `await session.list_tools()` 返回 4 个工具，名字/描述正确
   - 测试 `await session.call_tool("save_note", {"title": "t", "content": "c"})` 返回 `"Saved note 't' (1 chars)."`
   - 验证副作用：`tmp_path` 下有 `data/notes.json` 写入
3. 跑 `pytest tests/integration/test_mcp_stdio.py` → **失败**（`notes_server.py` 不存在）
4. `git add . && git commit -m "test: add integration test for MCP stdio server"`

**GREEN 步骤**

1. 创建 `servers/notes_server.py`，4 个 `@mcp.tool()` 包装 `notes_store` 的函数
2. 跑 `pytest` → **集成测试全过**
3. 跑 `pytest --cov=servers` → **覆盖率 100%**
4. `git add . && git commit -m "feat: implement notes MCP server with FastMCP"`

**IMPROVE 步骤**：可能改 docstring 让 LLM 更好理解

**验收**：
- [ ] 集成测试全过
- [ ] 4 个工具被发现且能调通
- [ ] JSON 文件被真实写入（不是 mock）
- [ ] `code-reviewer` 通过

---

## T3: config 模块

**目标文件**：`src/config.py`, `tests/unit/test_config.py`

**RED 步骤**

1. 创建 `tests/unit/test_config.py`，6 个测试：
   - `test_build_llm_cfg_returns_dict_with_required_keys`
   - `test_build_llm_cfg_missing_api_key_raises_keyerror`
   - `test_build_llm_cfg_missing_model_raises_keyerror`
   - `test_load_mcp_config_parses_valid_json`
   - `test_load_mcp_config_missing_top_level_key_raises_valueerror`
   - `test_load_mcp_config_nonexistent_file_raises_filenotfounderror`
2. 用 `monkeypatch.setenv` 注入 env，用 `tmp_path` 注入 mcp.json
3. 跑 → **全部失败**
4. `git commit -m "test: add failing tests for config module"`

**GREEN 步骤**

1. 创建 `src/config.py`：`load_env() / build_llm_cfg() / load_mcp_config() / validate_mcp_config() / SYSTEM_PROMPT / PROJECT_ROOT`
2. 跑 → **6 个测试全过**
3. `git commit -m "feat: implement config module with env loading and validation"`

**验收**：
- [ ] 6 个测试全过
- [ ] 覆盖率 100%

---

## T4: Assistant 构造

**目标文件**：`run_web.py`（部分）, `tests/integration/test_assistant_setup.py`

**RED 步骤**

1. 创建 `tests/integration/test_assistant_setup.py`：
   - mock `qwen_agent.tools.MCPManager.initConfig`（patch 在 `qwen_agent.tools.MCPManager` 命名空间下）
   - 构造 `Assistant(llm={"model": "x", "model_server": "http://x", "api_key": "x"}, function_list=[mcp_cfg], system_message="x")`
   - 断言 `initConfig` 被调用 1 次，参数为 `mcp_cfg` 字典
2. 注意：避免真实 LLM 调用 — 可以构造完即销毁，不调 `bot.run()`
3. 跑 → **失败**
4. `git commit -m "test: add integration test for Assistant MCP wiring"`

**GREEN 步骤**

1. 在 `run_web.py` 中：
   - `load_env()` 调用
   - 导入 `Assistant`
   - `build_bot()` 函数返回 `Assistant`
2. 跑 → **测试过**
3. `git commit -m "feat: wire Assistant with MCP config and system prompt"`

**验收**：
- [ ] 集成测试过
- [ ] 无真实网络/子进程调用
- [ ] mock 验证 `initConfig` 被调

---

## T5: WebUI 启动

**目标文件**：`run_web.py`（补全）, `tests/integration/test_webui_launch.py`

**RED 步骤**

1. 创建 `tests/integration/test_webui_launch.py`：
   - mock `WebUI.launch` 接受 `(server_port=..., inbrowser=False)` kwargs
   - 调 `build_bot()` 后调 `WebUI(bot).launch(server_port=0, inbrowser=False, prevent_thread_lock=True)`
   - 断言 mock 被调
2. 跑 → **失败**
3. `git commit -m "test: add integration test for WebUI launch"`

**GREEN 步骤**

1. 补全 `run_web.py` 的 `main()`：
   ```python
   def main() -> None:
       load_env()
       bot = build_bot()
       WebUI(bot).launch()
   ```
2. 加 `if __name__ == "__main__": main()`
3. 跑 → **测试过**
4. `git commit -m "feat: launch qwen-agent built-in WebUI from run_web.py"`

**验收**：
- [ ] 测试过
- [ ] 实际启动：`python run_web.py` → 浏览器可访问 7860

---

## T6: README + 冒烟脚本

**目标文件**：`README.md`, `scripts/smoke_test.py`, `.env.example`

**commit**：`docs: add README with install, run, demo queries, troubleshooting`

内容：
- README：项目简介 → 安装 → 配置 → 运行 → 4 条演示 Query → 故障排查 → 链接到 `docs/specs/`
- `scripts/smoke_test.py`：拉起 notes_server.py 子进程，调 `save_note` + `read_note` + 验证 JSON 文件
- `.env.example`：3 个变量模板

**验收**：
- [ ] `python scripts/smoke_test.py` 跑通
- [ ] 4 条演示 Query 文档清晰

---

## 时间线（参考）

| 阶段 | 预计 commit 数 | 预计时长 |
|---|---|---|
| Phase 1（SDD） | 1 | 30 分钟 |
| Phase 2（Skeleton） | 1 | 15 分钟 |
| Phase 3 T1-T6 | 10-12 | 4-6 小时 |
| 验证 + 修整 | 1-2 | 1 小时 |

总预计：12-15 个 commit，6-8 小时。
