# 01 - 代码规范与约定

> Status: Approved
> 适用范围: 仓库内所有 Python 代码、文档、Git 提交

## 1. Python 风格

### 1.1 命名

| 类型 | 风格 | 例子 |
|---|---|---|
| 文件 / 模块 | snake_case | `notes_store.py` |
| 类 | PascalCase | `NotesStore`, `MCPClient` |
| 函数 / 方法 / 变量 | snake_case | `save_one()`, `notes_file` |
| 常量 | UPPER_SNAKE_CASE | `MAX_TITLE_LEN = 200` |
| 私有成员 | 前缀 `_` | `_load_internal` |
| 布尔 | `is_` / `has_` / `can_` | `is_valid`, `has_notes` |

### 1.2 不可变性（关键）

- 列表、字典等可变数据**不要就地修改**，函数返回新对象
- 例外：纯内部函数、不跨边界时可原地操作，但需在 docstring 说明

```python
# 错误
def add_note(notes: dict, k: str, v: str) -> None:
    notes[k] = v  # 副作用

# 正确
def with_note(notes: dict, k: str, v: str) -> dict:
    return {**notes, k: v}
```

### 1.3 函数与文件

- 函数 < 50 行
- 文件 < 800 行
- 嵌套深度 ≤ 4 层（超则用 early return）
- 每个公共函数必须有 docstring（Google 风格）

### 1.4 错误处理

- 不要静默吞错
- 顶层边界（CLI 入口、API 入口）捕获后输出用户友好消息 + 详细 traceback 到日志
- 业务函数用返回码或抛特定异常，不混用

### 1.5 输入校验

- 系统边界（env 读取、文件读取、用户输入）必须校验
- JSON 文件损坏 → 返回 `{}` 而非崩溃
- env 缺失 → 抛 `KeyError` 且消息含变量名

### 1.6 类型注解

- 所有公共函数必须有类型注解
- 内部函数可省略
- 第三方库无类型时用 `Any` 标注

### 1.7 导入

顺序（每组间空一行）：

```python
from __future__ import annotations

# 1. 标准库
import json
from pathlib import Path

# 2. 第三方
from dotenv import load_dotenv

# 3. 本地
from src.config import PROJECT_ROOT
```

## 2. 目录结构

```
D:\project\demo-qwenagent-mcp\
├── docs/specs/        # 规范（SSOT）
├── src/               # 业务代码
│   ├── config.py
│   └── notes_store.py
├── servers/           # MCP 服务
├── tests/
│   ├── unit/          # 纯函数单测
│   └── integration/   # 子进程 / 集成测试
├── scripts/           # 一次性脚本（手动跑）
├── run_web.py         # 入口
├── mcp.json
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── conda-env.yml
├── .env.example
├── .gitignore
└── README.md
```

## 3. 测试规范

- 用 `pytest`，不用 `unittest`
- 文件名 `test_*.py`，函数名 `test_*`
- AAA 模式（Arrange / Act / Assert）
- 每个测试独立，不依赖其他测试的副作用
- 用 `tmp_path` fixture 隔离文件系统
- 用 `monkeypatch` 隔离全局状态
- 不 mock 自己要测的层（如不 mock MCP 协议层）

## 4. Git 规范

### 4.1 提交格式（Conventional Commits）

```
<type>(<scope>): <subject>

<body>（可选）

<footer>（可选）
```

**type 必须是以下之一**：

| type | 用途 | 例子 |
|---|---|---|
| `feat` | 新功能 | `feat: add notes CRUD store` |
| `fix` | 修 bug | `fix: handle missing .env gracefully` |
| `test` | 仅测试 | `test: add unit tests for notes_store` |
| `refactor` | 重构（无功能变化） | `refactor: extract JSON path resolution` |
| `docs` | 文档 | `docs: add SDD specification` |
| `chore` | 杂项 | `chore: scaffold project structure` |
| `perf` | 性能 | `perf: batch JSON writes` |
| `ci` | CI 配置 | `ci: add GitHub Actions workflow` |

### 4.2 提交粒度

- 一个 commit 只做一件事
- RED 测试单独 commit：`test: add failing tests for X`
- GREEN 实现单独 commit：`feat: implement X`
- 重构单独 commit：`refactor: ...`
- 提交前必须用 `code-reviewer` 子代理审查

### 4.3 安全约束（用户硬性规则）

- **禁止** `git filter-repo` / `git filter-branch`
- **禁止** `git push --force`（除非明确知道且有远程备份）
- **禁止** `git reset --hard`（除非有未提交的不需要保留）
- **禁止** `git rebase`（除非明确知道后果）
- 任何重写历史前先 `git bundle create backup.bundle --all`

## 5. 文档规范

- 文档用 Markdown
- 标题用 ATX 风格（`#` 开头）
- 列表用 `-` 不用 `*`
- 代码块指定语言（```python、```bash）

## 6. 环境与依赖

- Python ≥ 3.10（GUI 最低要求）
- 包管理：conda（环境名 `qwenagent-mcp`）
- 运行命令：`conda run -n qwenagent-mcp python <script>`
- 依赖在 `requirements.txt` 和 `requirements-dev.txt`，**不**写死在代码里

## 7. 禁止事项

- ❌ 在代码中硬编码 API key、token、密码
- ❌ 提交 `.env` 文件
- ❌ 在 `print` 中输出敏感信息
- ❌ 用 `print` 做日志（用 `logging`）
- ❌ 写 `pass` 占位的 TODO 块（用 `raise NotImplementedError`）
