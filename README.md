# CLI Hub

> 企业 CLI 统一网关 — Agent 只装一个 Skill，就能操作所有企业平台。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)

## 为什么需要 CLI Hub？

国内大厂纷纷开放了 CLI + Agent Skill：
- [企业微信 wecom-cli](https://github.com/WecomTeam/wecom-cli) — 7 大品类、12 个 Skills
- [钉钉 dws](https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli) — 12 个产品、86 个命令
- [飞书 lark-cli](https://github.com/larksuite/cli) — 11 个业务域、200+ 命令、19 个 Skills

但从用户角度，要分别安装和维护这些 CLI + Skill 非常麻烦。**CLI Hub 把它们统一管理**，用户只需一个工具 + 一个 Skill，就可以**搜索、安装、认证、调用**所有企业平台的工具。

## 特性

- **语义搜索** — 中英文混合搜索 300+ 工具，基于 jieba + BM25
- **一键安装** — `cli-hub install --all` 自动安装所有底层 CLI
- **统一认证** — `cli-hub auth <provider>` 委托各 CLI 原生认证流程
- **统一调用** — `cli-hub run <operation_id> [args]` 一条命令调用任何工具
- **Agent 友好** — 配套 SKILL.md，Agent 开箱即用
- **可扩展** — 新增厂商只需添加 JSON schema + adapter

## 安装

**一键安装（推荐）：**

```bash
curl -sSL https://raw.githubusercontent.com/agentrix-ai/clihub/main/install.sh | bash
```

自动检测环境，选择最优方式安装（uv > pipx > pip），没有 Python 也会尝试自动安装。

**手动安装：**

```bash
pip install agent-cli-hub     # pip
pipx install agent-cli-hub    # pipx
uv tool install agent-cli-hub # uv
```

**从源码：**

```bash
git clone https://github.com/agentrix-ai/clihub.git
cd clihub
uv sync
```

## 快速开始

```bash
# 1. 检查环境
cli-hub doctor

# 2. 安装底层 CLI（按需）
cli-hub install lark
cli-hub install dingtalk
cli-hub install wecom

# 3. 认证
cli-hub auth lark
cli-hub auth dingtalk

# 4. 搜索工具
cli-hub search "发送消息给同事"
cli-hub search "创建待办" --provider lark

# 5. 调用
cli-hub run lark.calendar.agenda
cli-hub run wecom.todo.create_todo '{"content":"写周报"}'
cli-hub run dingtalk.contact.user_search --keyword "悟空"
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `cli-hub search <query>` | 语义搜索工具（支持 `--provider`, `--category`, `--top`, `--json`） |
| `cli-hub install <provider>` | 安装底层 CLI（支持 `--all`） |
| `cli-hub auth <provider>` | 认证（支持 `--status`） |
| `cli-hub run <operation_id> [args]` | 调用工具 |
| `cli-hub list [provider]` | 列出 provider / 工具 |
| `cli-hub doctor` | 诊断环境 |
| `cli-hub refresh [provider]` | 从 CLI 动态刷新 schema |
| `cli-hub version` | 版本信息 |

## 支持的平台

| 平台 | Provider | CLI | 工具数 |
|------|----------|-----|--------|
| 企业微信 | `wecom` | wecom-cli | 27 |
| 钉钉 | `dingtalk` | dws | 23 |
| 飞书 | `lark` | lark-cli | 27 |

## 扩展

新增一个 CLI 厂商只需：

1. 添加 `schemas/<name>.json` — 工具 schema
2. 添加 `cli_gateway/adapters/<name>.py` — adapter 实现
3. 在 `registry.py` 注册 Provider

## Agent Skill

将 `skills/SKILL.md` 安装到 Agent 环境即可使用：

```bash
cp skills/SKILL.md ~/.cursor/skills/cli-hub/SKILL.md
```

## License

MIT
