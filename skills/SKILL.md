---
name: cli-hub
description: >-
  Unified CLI gateway to search, install, authenticate, and invoke enterprise,
  developer, and AI platform tools (WeCom, DingTalk, Lark/Feishu, Dreamina/即梦,
  Google Workspace, GitHub CLI, npm, React Native) covering 150+ operations.
  Use when the user mentions 企业微信/WeCom, 钉钉/DingTalk, 飞书/Lark/Feishu,
  即梦/Dreamina, Google Workspace/Gmail/Drive/Sheets, GitHub/gh, npm,
  React Native, or needs to send messages, manage calendars, todos, contacts,
  documents, meetings, generate images/videos, manage repos/PRs/issues,
  manage npm packages, or build mobile apps.
---

# cli-hub — 企业 & 开发者 CLI 统一网关

一个 Skill 搜索和调用所有企业平台、开发者工具和 AI 创作工具，覆盖 150+ 工具。

## 安装 cli-hub

**先检查是否已安装：**

```bash
cli-hub version
```

- 如果输出版本号 → 已安装，跳过安装步骤，直接进入「标准工作流」。
- 如果 `command not found` → 未安装，执行下方安装命令。

**推荐（从 PyPI 安装，有包签名验证）：**

```bash
pip install agent-cli-hub     # pip
pipx install agent-cli-hub    # pipx（隔离环境）
uv tool install agent-cli-hub # uv
```

> PyPI: https://pypi.org/project/agent-cli-hub/
> Source: https://github.com/agentrix-ai/clihub (MIT License)

**备选（一键脚本，内部调用 pip 从 PyPI 安装）：**

```bash
curl -sSL https://raw.githubusercontent.com/agentrix-ai/clihub/main/install.sh | bash
```

## 强制规则

1. **禁止猜命令** — 必须先 `cli-hub search` 找到工具 ID。
2. **调用前查参数** — 必须先 `cli-hub info <id>` 确认参数 schema。
3. **安装底层 CLI 只用 `cli-hub install`** — 禁止自行用 pip/npm/brew 安装底层 CLI（如 dreamina、wecom-cli 等）。每个 provider 有专属安装方式，`cli-hub install <provider>` 已内置正确的安装命令。
4. 出错时查阅下方「错误处理」表，按指引修复。

## 标准工作流

严格按 Step 1 → 2 → 3 → 4 顺序执行。

### Step 1: 检查环境（每次必做）

```bash
cli-hub doctor
```

根据输出**逐个判断**，只处理有问题的 provider，已就绪的跳过：
- `installed ✓ / authenticated ✓` → **已就绪，不需要任何操作**
- `not installed` → 仅安装该 provider
- `installed` 但 `not authenticated` → 仅认证该 provider
- 全部 OK → 直接跳到 Step 2

**安装底层 CLI（仅安装 doctor 显示 `not installed` 的）：**

```bash
cli-hub install wecom              # 企业微信 (npm)
cli-hub install dingtalk           # 钉钉 (curl script)
cli-hub install lark               # 飞书 (npm)
cli-hub install dreamina           # 即梦 AI (curl script)
cli-hub install gws                # Google Workspace (npm)
cli-hub install gh                 # GitHub CLI (brew/apt)
cli-hub install npm                # npm (随 Node.js 自带)
cli-hub install react-native       # React Native CLI (npm)
cli-hub install --all              # 全部未安装的
cli-hub install lark --timeout 300 # 网络慢时加大超时（默认 180s）
```

> **重要：不要自行用 pip/npm/brew 安装底层 CLI，统一用 `cli-hub install`。已安装的不要重复安装。**

**认证（仅认证 doctor 显示未认证的，交互式需用户参与）：**

```bash
cli-hub auth wecom
cli-hub auth dingtalk
cli-hub auth lark
cli-hub auth dreamina              # 即梦（终端扫码登录）
cli-hub auth gws                   # Google Workspace（OAuth 浏览器授权）
cli-hub auth gh                    # GitHub（浏览器或 token 认证）
cli-hub auth npm                   # npm login
cli-hub auth --status              # 查看所有认证状态
```

### Step 2: 搜索工具

```bash
cli-hub search "发送消息给同事"
cli-hub search "创建待办" --provider lark
cli-hub search "生成视频" --provider dreamina
cli-hub search "create PR" --provider gh
cli-hub search "send email" --provider gws
cli-hub search "会议" --json        # Agent 推荐：JSON 输出含 input_schema
```

### Step 3: 查看参数

```bash
cli-hub info wecom.msg.send_message        # 表格格式
cli-hub info wecom.msg.send_message --json # Agent 推荐：完整 JSON Schema
```

输出包含：参数名、类型、是否必填（`*` 标记）、调用示例、底层命令模板。

### Step 4: 调用工具

**方式 A — JSON 参数（wecom 风格）：**

```bash
cli-hub run wecom.msg.send_message --args '{"chat_type":1,"chatid":"user1","msgtype":"text","text":{"content":"hello"}}'
```

**方式 B — Flag 参数（dingtalk / lark / dreamina 风格）：**

```bash
cli-hub run lark.im.messages_send --chat-id oc_xxx --text "Hello"
cli-hub run dingtalk.todo.task_create --title "写周报" --executors userId
cli-hub run dreamina.generate.text2image --prompt "a cat portrait" --ratio 1:1
cli-hub run gh.pr.create --title "Add feature" --base main
cli-hub run gws.gmail.send --to alice@example.com --subject "Hello" --body "Hi"
cli-hub run npm.package.install --package express
```

**如何判断用哪种？** `cli-hub info <id>` 的 Example 字段会显示底层 CLI 的参数风格。

## 辅助命令

| 命令 | 用途 |
|------|------|
| `cli-hub list` | 列出所有 provider |
| `cli-hub list lark` | 列出飞书所有工具 |
| `cli-hub list dingtalk --category todo` | 按分类过滤 |
| `cli-hub refresh` | 从 clihub.cc 拉取最新 schema + 刷新本地 |
| `cli-hub refresh --no-remote` | 仅刷新本地，不联网 |
| `cli-hub add <binary> --display "Name"` | 添加新 CLI provider |

## 决策树

```
用户意图
├── 不确定用哪个平台 → cli-hub search "<描述>"
├── 知道平台不知道工具 → cli-hub list <provider>
├── 找到工具 ID → cli-hub info <id> → cli-hub run <id> [args]
├── "not installed" → cli-hub install <provider>
├── "not authenticated" → cli-hub auth <provider>
├── "Operation not found" → cli-hub search 重新搜索
├── "timed out" → cli-hub install <provider> --timeout 300
└── 环境不确定 → cli-hub doctor
```

## 错误处理

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `not installed` | CLI 未安装 | `cli-hub install <provider>` |
| `not authenticated` | 未认证 | `cli-hub auth <provider>` |
| `Operation not found` | ID 拼写错误 | `cli-hub search` 重新搜索 |
| `No adapter registered` | provider 名错误 | `cli-hub list` 查看可用名 |
| `timed out after Ns` | 超时 | 加 `--timeout 300` 重试 |
| `Invalid JSON` | --args JSON 格式错误 | 检查引号和转义 |
| 底层 CLI 业务错误 | 参数不对或权限不足 | `cli-hub info <id>` 查参数 |

## 支持的平台

### 企业协作

| 平台 | Provider | 工具数 | 覆盖领域 |
|------|----------|-------|---------|
| 企业微信 | wecom | 28 | 通讯录、待办、会议、消息、日程、文档、智能表格 |
| 钉钉 | dingtalk | 23 | 通讯录、群聊、日历、待办、审批、考勤、日志、智能表格 |
| 飞书 | lark | 28 | 日历、消息、文档、云盘、多维表格、电子表格、任务、Wiki、邮件、会议 |
| Google Workspace | gws | 20 | Drive、Gmail、Calendar、Sheets、Docs、Chat、Workflow |

### 开发者工具

| 平台 | Provider | 工具数 | 覆盖领域 |
|------|----------|-------|---------|
| GitHub CLI | gh | 20 | 仓库、PR、Issue、Release、Actions、Gist、搜索、API |
| npm | npm | 16 | 包安装/发布/搜索/审计、项目初始化/运行、安全检查 |
| React Native | react-native | 12 | 创建项目、Metro 开发服务器、iOS/Android 构建运行、诊断 |

### AI 创作

| 平台 | Provider | 工具数 | 覆盖领域 |
|------|----------|-------|---------|
| 即梦 | dreamina | 12 | 文生图、文生视频、图生图、图生视频、多模态视频、图片超分、Seedance 2.0 |

## 注意

- 认证是交互式的，Agent 应提示用户手动完成浏览器授权
- 即梦 Agent 登录推荐 `dreamina login --headless`（终端扫码），生成操作消耗积分需提前告知用户
- 即梦生成任务是异步的：提交后用 `query_result --submit_id=<id>` 查询结果
- 搜索结果按相关性排序，优先使用得分最高的工具
- 逐个调用工具并确认结果，不要批量调用
- `cli-hub refresh` 会自动从 https://clihub.cc 拉取最新工具列表，新增 provider 无需升级 cli-hub
