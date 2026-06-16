# 02 - 需求规格说明

> Status: Approved
> 范围: Demo 项目 v0.1.0

## 1. 项目目标

演示 **Qwen Agent** 通过 **MCP（Model Context Protocol）** 调用外部工具的完整链路，重点展示：

1. 自定义 MCP 服务的写法
2. Qwen Agent 通过 MCP 发现并调用工具
3. 工具调用的端到端可观测（不只是 LLM 输出）

## 2. 功能需求（FR）

### FR-1: 笔记工具集

提供 4 个工具，签名如下：

| 工具 | 输入 | 输出 | 副作用 |
|---|---|---|---|
| `save_note(title, content)` | 标题（str）、内容（str） | `"Saved note '<title>' (<n> chars)."` | 写入/覆盖 `data/notes.json` |
| `read_note(title)` | 标题（str） | 内容（str）或 `"Note '<title>' not found."` | 无 |
| `list_notes()` | 无 | 多行字符串 `"<title> (<n> chars)\n..."` 或 `"No notes saved yet."` | 无 |
| `delete_note(title)` | 标题（str） | `"Deleted note '<title>'."` 或 `"Note '<title>' not found."` | 删除 JSON 中的键 |

### FR-2: 笔记持久化

- 存储位置：`<项目根>/data/notes.json`
- 格式：`{"<title>": "<content>", ...}`，UTF-8 编码，2 空格缩进
- 进程重启后能读回
- JSON 损坏时回退为空字典（不崩溃）

### FR-3: WebUI 启动

- 入口命令：`conda run -n qwenagent-mcp python run_web.py`
- 启动后 Gradio 在 `http://127.0.0.1:7860` 可访问
- 工具列表在 UI 侧栏可见

### FR-4: Agent 工具调用

- 用户 Query → Agent 决定调用哪个工具 → 实际执行 → 结果返回 → 最终回答
- 4 条演示 Query 全部按预期序列执行

## 3. 非功能需求（NFR）

| ID | 需求 | 验证方式 |
|---|---|---|
| NFR-1 | 冷启动 < 10 秒 | 手测 + 集成测试 |
| NFR-2 | 测试覆盖率 ≥ 80% | `pytest --cov` |
| NFR-3 | 唯一外部依赖是 conda | `conda-env.yml` 一键复现 |
| NFR-4 | 至少 12 个原子 commit | `git log --oneline` |
| NFR-5 | 无硬编码密钥 | `grep -r "sk-" .` 不命中（除 `.env.example`） |
| NFR-6 | 所有公共函数有类型注解 | `mypy` 检查通过 |

## 4. 验收标准

### 4.1 自动化验收

- [ ] `pytest` 全部通过
- [ ] `pytest --cov=src --cov=servers --cov-report=term` 显示覆盖率 ≥ 80%
- [ ] `scripts/smoke_test.py` 跑通（拉起子进程，save+read 成功）

### 4.2 手动验收（演示 Query）

| # | Query | 期望工具调用序列 |
|---|---|---|
| Q1 | "Save a note titled `meeting` with content '3pm demo'. Then list all my notes." | `save_note` → `list_notes` |
| Q2 | "What did I write in the `meeting` note?" | `read_note` |
| Q3 | "Append ' — agenda: X' to the `meeting` note, then read it back." | `read_note` → `save_note` → `read_note` |
| Q4 | "Delete the `meeting` note and confirm by listing." | `delete_note` → `list_notes` |

4 条全部按预期序列返回 → 验收通过。

## 5. 范围外（Non-goals）

- ❌ 多用户并发支持
- ❌ 笔记加密/权限
- ❌ 笔记搜索/标签/分类
- ❌ WebUI 自定义（用 qwen-agent 内置）
- ❌ 多个 LLM 后端同时支持
- ❌ Docker 化部署
- ❌ CI/CD 流水线（可选）

## 6. 风险与假设

| 风险 | 缓解 |
|---|---|
| MiniMax API base URL 在当前环境无法独立验证 | `.env` 暴露 base URL，便于调整 |
| `qwen-agent` GUI 在某些 Windows 环境下端口冲突 | 启动失败时打印明确错误信息，文档列出 `server_port=` 改端口方法 |
| MiniMax-M3 function-calling 能力未知 | `system_message` 强化指令；若失败，文档列出换模型步骤 |
| FastMCP 版本差异导致 API 不同 | `requirements.txt` pin 最低版本；测试用真实子进程验证 |
