# CLI Hub — 工程指导纲领

## 项目定位

**clihub** 是一个统一的企业 CLI 网关工具，Agent 只装一个 Skill 就能搜索、安装、认证、调用 WeCom / DingTalk / Lark 等多家大厂的 CLI 工具。

## 技术栈

- Python 3.10+ / Hatchling 构建
- CLI: typer + rich
- 搜索: jieba (中文分词) + BM25
- 模型: pydantic
- 异步: asyncio (subprocess 调用底层 CLI)
- 包管理: uv

## 架构

```
Agent → SKILL.md → clihub CLI → Dispatcher → Adapter(wecom/dingtalk/lark) → subprocess → 底层 CLI
```

核心概念:
- **Provider**: 一个 CLI 厂商 (wecom/dingtalk/lark)，配置在 Registry 中
- **Operation**: 一个可调用的工具，ID 格式 `provider.category.name`
- **Adapter**: 将统一接口翻译为各 CLI 的 argv
- **Registry**: 加载/缓存所有 Operation 的 Schema (JSON 文件)

## 目录结构

- `cli_gateway/cli.py` — 主 CLI 命令 (search/install/auth/run/list/info/doctor/refresh/add/version)
- `cli_gateway/core/registry.py` — Schema Registry + Provider 注册
- `cli_gateway/core/dispatcher.py` — 路由到 Adapter
- `cli_gateway/core/search.py` — BM25 搜索引擎
- `cli_gateway/core/schema_extractor.py` — 自动抽取 schema（从 schema 命令 / --help）
- `cli_gateway/adapters/` — 三个专用 Adapter + GenericAdapter（通用）
- `cli_gateway/models/` — Operation + Provider Pydantic 模型
- `schemas/` — 静态 Schema JSON (每家一个文件)
- `skills/SKILL.md` — Agent Skill 定义

## 扩展新 Provider

**自动方式（推荐）**:
```bash
clihub add <binary> --display "Name" --install-cmd "..." --schema-cmd "..."
```
自动从 `schema` 命令或 `--help` 抽取工具列表，生成 `schemas/<name>.json`，用 GenericAdapter 调用。

**手动方式**:
1. 在 `schemas/` 下新增 `<name>.json`
2. 在 `cli_gateway/core/registry.py` 的 `BUILTIN_PROVIDERS` 中添加 Provider
3. （可选）写专用 adapter，否则自动用 GenericAdapter

## 运行

```bash
uv sync
uv run clihub --help
uv run clihub search "发消息"
uv run clihub doctor
```

## 测试

```bash
uv run pytest tests/ -v
```
