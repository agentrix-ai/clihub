# CLI Hub — 工程指导纲领

## 项目定位

**cli-hub** 是一个统一的企业 & 开发者 CLI 网关工具，Agent 只装一个 Skill 就能搜索、安装、认证、调用 WeCom / DingTalk / Lark / Dreamina / Google Workspace / GitHub CLI / npm / React Native 等 8 大平台 150+ 工具。

## 技术栈

- Python 3.10+ / Hatchling 构建
- CLI: typer + rich
- 搜索: jieba (中文分词) + BM25
- 模型: pydantic
- 异步: asyncio (subprocess 调用底层 CLI)
- 包管理: uv
- 网站: FastAPI + Jinja2（website/ 目录）

## 架构

```
Agent → SKILL.md → cli-hub CLI → Dispatcher → Adapter(wecom/dingtalk/lark/dreamina/gws/gh/npm/react-native) → subprocess → 底层 CLI

Schema 加载优先级:
  ~/.cli-hub/schemas/ (远程缓存) > cli_gateway/schemas/ (包内 fallback)

Schema 远程注册:
  cli-hub refresh → GET https://clihub.cc/api/schemas → 存入 ~/.cli-hub/schemas/
```

核心概念:
- **Provider**: 一个 CLI 厂商 (wecom/dingtalk/lark/dreamina/gws/gh/npm/react-native)，配置在 Registry 中
- **Operation**: 一个可调用的工具，ID 格式 `provider.category.name`
- **Adapter**: 将统一接口翻译为各 CLI 的 argv
- **Registry**: 加载/缓存所有 Operation 的 Schema (JSON 文件)
- **Schema Registry (clihub.cc)**: 远程 schema 注册表，新增 provider 无需发 PyPI

## 目录结构

- `cli_gateway/cli.py` — 主 CLI 命令 (search/install/auth/run/list/info/doctor/refresh/add/version)
- `cli_gateway/core/registry.py` — Schema Registry + Provider 注册 + 远程缓存
- `cli_gateway/core/dispatcher.py` — 路由到 Adapter
- `cli_gateway/core/search.py` — BM25 搜索引擎
- `cli_gateway/core/schema_extractor.py` — 自动抽取 schema（从 schema 命令 / --help）
- `cli_gateway/adapters/` — 三个专用 Adapter (wecom/dingtalk/lark) + GenericAdapter（其余全用通用）
- `cli_gateway/models/` — Operation + Provider Pydantic 模型
- `cli_gateway/schemas/` — 包内静态 Schema JSON (fallback)
- `skills/SKILL.md` — Agent Skill 定义（中文）
- `skills/SKILL_EN.md` — Agent Skill 定义（英文）
- `skills/INTEGRATION_SOP.md` — 新 CLI 集成 SOP（标准化流程 Skill）
- `website/` — clihub.cc 网站 + Schema Registry API
  - `website/app.py` — FastAPI 主应用
  - `website/schemas/` — 服务器上的 Schema source of truth
  - `website/templates/` — Landing page (Jinja2)
  - `website/deploy.sh` — 一键部署脚本

## 扩展新 Provider

**方式 1: 远程注册（推荐，无需发 PyPI）**
1. 在 `website/schemas/` 下新增 `<name>.json`
2. 在 `website/schemas/providers.json` 中添加元数据
3. 部署网站: `cd website && bash deploy.sh`
4. 用户执行 `cli-hub refresh` 即可获取

**方式 2: 自动抽取**
```bash
cli-hub add <binary> --display "Name" --install-cmd "..." --schema-cmd "..."
```

**方式 3: 手动**
1. 在 `cli_gateway/schemas/` 下新增 `<name>.json`
2. 在 `cli_gateway/core/registry.py` 的 `BUILTIN_PROVIDERS` 中添加
3. 发布新版本到 PyPI

## 网站 (clihub.cc)

- **域名**: https://clihub.cc
- **服务器**: 47.76.201.162（阿里云香港）
- **端口**: 18010（uvicorn）
- **systemd**: `clihub-web.service`
- **nginx**: 反代 + SSL (Let's Encrypt)
- **部署**: `cd website && bash deploy.sh`

## 运行

```bash
uv sync
uv run cli-hub --help
uv run cli-hub search "发消息"
uv run cli-hub doctor
uv run cli-hub refresh          # 从 clihub.cc 拉最新 schema
```

## 测试

```bash
uv run pytest tests/ -v         # 128+ tests
```
