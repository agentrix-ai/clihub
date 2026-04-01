# clihub — 企业 CLI 统一网关

一个 Skill 搜索和调用所有企业平台工具（企业微信 / 钉钉 / 飞书），覆盖 79+ 工具。

## 使用时机

用户提到以下任何一个平台或场景时，使用本 Skill：
- **企业微信 (WeCom)**：通讯录、待办、会议、消息、日程、文档、智能表格
- **钉钉 (DingTalk)**：通讯录、群聊、日历、待办、审批、考勤、日志、智能表格
- **飞书 (Lark/Feishu)**：日历、消息、文档、云盘、多维表格、电子表格、任务、Wiki、邮件、会议

## 强制规则

1. **永远先搜索，禁止猜命令。** 必须用 `clihub search` 找到工具 ID 后再调用。
2. **调用前必须用 `clihub info` 查看参数。** 不要凭记忆拼参数。
3. **所有命令前加 `uv run`**（除非用户已全局安装）。

## 标准工作流（严格按顺序执行）

### Step 1: 检查环境（首次使用必做）

```bash
uv run clihub doctor
```

输出会显示每个平台的安装和认证状态。如果显示 "not installed"，执行 Step 1a；如果已安装但未认证，执行 Step 1b。

#### Step 1a: 安装缺失的 CLI

```bash
uv run clihub install wecom           # 安装企业微信 CLI
uv run clihub install dingtalk        # 安装钉钉 CLI
uv run clihub install lark            # 安装飞书 CLI
uv run clihub install --all           # 全部安装
uv run clihub install lark --timeout 300  # 网络慢时加大超时
```

#### Step 1b: 认证

```bash
uv run clihub auth wecom              # 企业微信认证
uv run clihub auth dingtalk           # 钉钉认证
uv run clihub auth lark               # 飞书认证（需两步：config init + login）
uv run clihub auth --status           # 查看所有认证状态
```

认证是交互式的，会引导用户在浏览器中完成授权。

### Step 2: 搜索工具

```bash
uv run clihub search "发送消息给同事"
uv run clihub search "创建待办" --provider lark
uv run clihub search "查看日程" --top 5
uv run clihub search "会议" --json         # Agent 推荐用 --json 格式
```

搜索支持中英文混合，返回工具 ID、描述、示例、相关性得分。

### Step 3: 查看工具参数（关键步骤）

```bash
uv run clihub info <operation_id>          # 人类可读
uv run clihub info <operation_id> --json   # Agent 推荐，返回完整 JSON Schema
```

info 会显示：
- 参数名、类型、是否必填（`*` 标记）
- 调用示例
- 底层命令模板

### Step 4: 调用工具

两种传参方式，取决于底层 CLI 风格：

**方式 A: --args JSON（适用于 wecom）**

```bash
uv run clihub run wecom.msg.send_message --args '{"chat_type":1,"chatid":"user1","msgtype":"text","text":{"content":"hello"}}'
```

**方式 B: --flag value 透传（适用于 dingtalk / lark）**

```bash
uv run clihub run lark.im.messages_send --chat-id oc_xxx --text "Hello"
uv run clihub run dingtalk.todo.task_create --title "写周报" --executors userId
```

**判断用哪种方式**：执行 `clihub info <id>`，看 Example 中底层 CLI 的参数风格。

## 辅助命令

```bash
uv run clihub list                         # 列出所有平台
uv run clihub list lark                    # 列出飞书所有工具
uv run clihub list dingtalk --category todo  # 按分类过滤
uv run clihub list wecom --json            # JSON 输出
uv run clihub refresh                      # 从已安装 CLI 刷新 schema
uv run clihub add <binary> --display "Name"  # 添加新 CLI 提供商
```

## 决策树

```
用户意图
├── 不确定用哪个平台 → clihub search "<自然语言描述>"
├── 知道平台不知道工具 → clihub list <provider>
├── 找到工具 ID 了 → clihub info <id> → clihub run <id> [args]
├── 报错 "not installed" → clihub install <provider>
├── 报错 "not authenticated" 或 auth 失败 → clihub auth <provider>
├── 报错 "Operation not found" → clihub search 重新搜索
├── 报错 "No adapter" → provider 未注册，检查是否拼写错误
├── 报错 "timed out" → clihub install <provider> --timeout 300
└── 不确定环境状态 → clihub doctor
```

## 错误处理

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `not installed` | 底层 CLI 未安装 | `clihub install <provider>` |
| `not authenticated` | 未认证 | `clihub auth <provider>` |
| `Operation not found` | 工具 ID 拼写错误 | `clihub search` 重新搜索 |
| `No adapter registered` | provider 名错误 | `clihub list` 查看可用 provider |
| `timed out after Ns` | 安装/执行超时 | 加 `--timeout 300` 重试 |
| `Invalid JSON` | --args 的 JSON 格式错误 | 检查引号和转义 |
| 底层 CLI 返回业务错误 | 参数不对或权限不足 | `clihub info <id>` 查参数，检查认证 |

## 支持的平台

| 平台 | Provider 名 | 工具数 | 覆盖领域 |
|------|------------|-------|---------|
| 企业微信 | wecom | 28 | 通讯录、待办、会议、消息、日程、文档、智能表格 |
| 钉钉 | dingtalk | 23 | 通讯录、群聊、日历、待办、审批、考勤、日志、智能表格 |
| 飞书 | lark | 28 | 日历、消息、文档、云盘、多维表格、电子表格、任务、Wiki、邮件、会议 |

## 重要提示

- 所有命令都在 `cli-gateway-py` 工程目录下执行（`uv run` 需要工程环境）
- 认证是交互式的，需要用户在浏览器中操作，Agent 应提示用户手动完成
- 搜索结果按相关性排序，优先使用得分最高的工具
- 不要一次调用多个工具，逐个调用并确认结果
