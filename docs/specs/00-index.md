# 规范文档总览

本目录是项目的**单一事实源（Single Source of Truth）**，所有代码、测试、提交都应能追溯到这里的某篇文档。

## 阅读顺序

| 顺序 | 文件 | 何时读 |
|---|---|---|
| 1 | [01-conventions.md](./01-conventions.md) | 写任何代码前 |
| 2 | [02-specification.md](./02-specification.md) | 了解要做什么 |
| 3 | [03-design.md](./03-design.md) | 了解怎么实现 |
| 4 | [04-tasks.md](./04-tasks.md) | 准备开工时 |
| 5 | [05-test-plan.md](./05-test-plan.md) | 写测试时 |

## 文档维护规则

- 任何代码或结构变更**必须**先更新对应规范文档，再写代码
- 规范与代码不一致时，**规范优先**（按规范修正代码）
- 每篇文档头部有 `Status` 字段：`Draft` / `Approved` / `Superseded`

## 仓库位置

`D:\project\demo-qwenagent-mcp`（Windows 路径）
