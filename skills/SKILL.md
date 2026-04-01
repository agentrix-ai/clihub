---
name: clihub
description: >-
  Unified CLI gateway to search, install, authenticate, and invoke enterprise
  platform tools (WeCom, DingTalk, Lark/Feishu) covering 79+ operations.
  Use when the user mentions 企业微信/WeCom, 钉钉/DingTalk, 飞书/Lark/Feishu,
  or needs to send messages, manage calendars, todos, contacts, documents,
  meetings, approvals, or attendance across these platforms.
---

# clihub — 企业 CLI 统一网关

一个 Skill 搜索和调用所有企业平台工具（企业微信 / 钉钉 / 飞书），覆盖 79+ 工具。

## 强制规则

1. **禁止猜命令** — 必须先 `clihub search` 找到工具 ID。
2. **调用前查参数** — 必须先 `clihub info <id>` 确认参数 schema。
3. **所有命令加 `uv run` 前缀**（除非用户已全局安装 clihub）。

## 标准工作流

严格按 Step 1 → 2 → 3 → 4 顺序执行。

### Step 1: 检查环境（首次必做）

```bash
uv run clihub doctor
```

根据输出判断：
- 显示 `not installed` → 执行安装（见下方）
- 显示 `installed` 但未认证 → 执行认证（见下方）
- 全部 OK → 跳到 Step 2

**安装：**

```bash
uv run clihub install wecom             # 企业微信
uv run clihub install dingtalk          # 钉钉
uv run clihub install lark              # 飞书
uv run clihub install --all             # 全部
uv run clihub install lark --timeout 300  # 网络慢时加大超时（默认 180s）
```

**认证（交互式，需用户在浏览器完成授权）：**

```bash
uv run clihub auth wecom
uv run clihub auth dingtalk
uv run clihub auth lark
uv run clihub auth --status             # 查看所有认证状态
```

### Step 2: 搜索工具

```bash
uv run clihub search "发送消息给同事"
uv run clihub search "创建待办" --provider lark
uv run clihub search "查看日程" --top 5
uv run clihub search "会议" --json       # Agent 推荐：JSON 输出含 input_schema
```

### Step 3: 查看参数

```bash
uv run clihub info wecom.msg.send_message          # 表格格式
uv run clihub info wecom.msg.send_message --json   # Agent 推荐：完整 JSON Schema
```

输出包含：参数名、类型、是否必填（`*` 标记）、调用示例、底层命令模板。

### Step 4: 调用工具

**方式 A — JSON 参数（wecom 风格）：**

```bash
uv run clihub run wecom.msg.send_message --args '{"chat_type":1,"chatid":"user1","msgtype":"text","text":{"content":"hello"}}'
```

**方式 B — Flag 参数（dingtalk / lark 风格）：**

```bash
uv run clihub run lark.im.messages_send --chat-id oc_xxx --text "Hello"
uv run clihub run dingtalk.todo.task_create --title "写周报" --executors userId
```

**如何判断用哪种？** `clihub info <id>` 的 Example 字段会显示底层 CLI 的参数风格。

## 辅助命令

| 命令 | 用途 |
|------|------|
| `clihub list` | 列出所有 provider |
| `clihub list lark` | 列出飞书所有工具 |
| `clihub list dingtalk --category todo` | 按分类过滤 |
| `clihub refresh` | 从已安装 CLI 刷新 schema |
| `clihub add <binary> --display "Name"` | 添加新 CLI provider |

## 决策树

```
用户意图
├── 不确定用哪个平台 → clihub search "<描述>"
├── 知道平台不知道工具 → clihub list <provider>
├── 找到工具 ID → clihub info <id> → clihub run <id> [args]
├── "not installed" → clihub install <provider>
├── "not authenticated" → clihub auth <provider>
├── "Operation not found" → clihub search 重新搜索
├── "timed out" → clihub install <provider> --timeout 300
└── 环境不确定 → clihub doctor
```

## 错误处理

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `not installed` | CLI 未安装 | `clihub install <provider>` |
| `not authenticated` | 未认证 | `clihub auth <provider>` |
| `Operation not found` | ID 拼写错误 | `clihub search` 重新搜索 |
| `No adapter registered` | provider 名错误 | `clihub list` 查看可用名 |
| `timed out after Ns` | 超时 | 加 `--timeout 300` 重试 |
| `Invalid JSON` | --args JSON 格式错误 | 检查引号和转义 |
| 底层 CLI 业务错误 | 参数不对或权限不足 | `clihub info <id>` 查参数 |

## 支持的平台

| 平台 | Provider | 工具数 | 覆盖领域 |
|------|----------|-------|---------|
| 企业微信 | wecom | 28 | 通讯录、待办、会议、消息、日程、文档、智能表格 |
| 钉钉 | dingtalk | 23 | 通讯录、群聊、日历、待办、审批、考勤、日志、智能表格 |
| 飞书 | lark | 28 | 日历、消息、文档、云盘、多维表格、电子表格、任务、Wiki、邮件、会议 |

## 注意

- 认证是交互式的，Agent 应提示用户手动完成浏览器授权
- 搜索结果按相关性排序，优先使用得分最高的工具
- 逐个调用工具并确认结果，不要批量调用
