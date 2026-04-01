---
name: cli-hub
description: >-
  Unified CLI gateway to search, install, authenticate, and invoke enterprise,
  developer, and AI platform tools (WeCom, DingTalk, Lark/Feishu, Dreamina,
  Google Workspace, GitHub CLI, npm, React Native) covering 150+ operations.
  Use when the user mentions WeCom, DingTalk, Lark, Feishu, Dreamina,
  Google Workspace/Gmail/Drive/Sheets, GitHub/gh, npm, React Native,
  or needs to send messages, manage calendars, todos, contacts, documents,
  meetings, generate images/videos, manage repos/PRs/issues, manage npm
  packages, or build mobile apps.
---

# cli-hub — Unified CLI Gateway

One Skill to search and invoke all enterprise, developer, and AI creation tools, covering 150+ tools.

## Install cli-hub

**Check if already installed first:**

```bash
cli-hub version
```

- If it prints a version number → already installed, skip to "Standard Workflow".
- If `command not found` → not installed, run one of the install commands below.

**Recommended (from PyPI, package signatures verified):**

```bash
pip install agent-cli-hub     # pip
pipx install agent-cli-hub    # pipx (isolated env)
uv tool install agent-cli-hub # uv
```

> PyPI: https://pypi.org/project/agent-cli-hub/
> Source: https://github.com/agentrix-ai/clihub (MIT License)

**Alternative (convenience script, internally runs pip from PyPI):**

```bash
curl -sSL https://raw.githubusercontent.com/agentrix-ai/clihub/main/install.sh | bash
```

## Mandatory Rules

1. **Never guess commands** — Always `cli-hub search` to find the tool ID first.
2. **Check params before calling** — Always `cli-hub info <id>` to confirm the parameter schema.
3. **Only use `cli-hub install` for underlying CLIs** — Do NOT install underlying CLIs (dreamina, wecom-cli, lark-cli, dws, etc.) via pip/npm/brew yourself. Each provider has a dedicated install method; `cli-hub install <provider>` has the correct command built in.
4. On error, consult the "Error Handling" table below.

## Standard Workflow

Follow Steps 1 → 2 → 3 → 4 strictly in order.

### Step 1: Check Environment (required every time)

```bash
cli-hub doctor
```

Check each provider's status **individually**; only act on those with issues, skip ready ones:
- `installed ✓ / authenticated ✓` → **Ready, no action needed**
- `not installed` → install only that provider
- `installed` but `not authenticated` → authenticate only that provider
- All OK → skip to Step 2

**Install underlying CLIs (only install those shown as `not installed` by doctor):**

```bash
cli-hub install wecom              # WeCom (npm)
cli-hub install dingtalk           # DingTalk (curl script)
cli-hub install lark               # Lark/Feishu (npm)
cli-hub install dreamina           # Dreamina AI (curl script)
cli-hub install gws                # Google Workspace (npm)
cli-hub install gh                 # GitHub CLI (brew/apt)
cli-hub install npm                # npm (bundled with Node.js)
cli-hub install react-native       # React Native CLI (npm)
cli-hub install --all              # All not-yet-installed
cli-hub install lark --timeout 300 # Increase timeout for slow networks
```

> **Important: Do NOT install underlying CLIs via pip/npm/brew yourself. Always use `cli-hub install`. Do NOT re-install already installed ones.**

**Authenticate (only for those shown as unauthenticated; interactive, requires user):**

```bash
cli-hub auth wecom
cli-hub auth dingtalk
cli-hub auth lark
cli-hub auth dreamina              # Dreamina (terminal QR code login)
cli-hub auth gws                   # Google Workspace (OAuth browser auth)
cli-hub auth gh                    # GitHub (browser or token auth)
cli-hub auth npm                   # npm login
cli-hub auth --status              # Check all auth status
```

### Step 2: Search Tools

```bash
cli-hub search "send message"
cli-hub search "create todo" --provider lark
cli-hub search "generate video" --provider dreamina
cli-hub search "create PR" --provider gh
cli-hub search "send email" --provider gws
cli-hub search "meeting" --json     # Recommended for agents: JSON with input_schema
```

### Step 3: Check Parameters

```bash
cli-hub info wecom.msg.send_message        # Table format
cli-hub info wecom.msg.send_message --json # Recommended for agents: full JSON Schema
```

Shows: parameter name, type, required (`*`), example, command template.

### Step 4: Invoke Tool

**Method A — JSON arguments (WeCom style):**

```bash
cli-hub run wecom.msg.send_message --args '{"chat_type":1,"chatid":"user1","msgtype":"text","text":{"content":"hello"}}'
```

**Method B — Flag arguments (DingTalk / Lark / Dreamina style):**

```bash
cli-hub run lark.im.messages_send --chat-id oc_xxx --text "Hello"
cli-hub run dingtalk.todo.task_create --title "Write report" --executors userId
cli-hub run dreamina.generate.text2image --prompt "a cat portrait" --ratio 1:1
cli-hub run gh.pr.create --title "Add feature" --base main
cli-hub run gws.gmail.send --to alice@example.com --subject "Hello" --body "Hi"
cli-hub run npm.package.install --package express
```

**How to choose?** `cli-hub info <id>` Example field shows the underlying CLI's argument style.

## Utility Commands

| Command | Purpose |
|---------|---------|
| `cli-hub list` | List all providers |
| `cli-hub list lark` | List all Lark tools |
| `cli-hub list dingtalk --category todo` | Filter by category |
| `cli-hub refresh` | Pull latest schemas from clihub.cc + refresh local |
| `cli-hub refresh --no-remote` | Refresh local only, no network |
| `cli-hub add <binary> --display "Name"` | Add a new CLI provider |

## Decision Tree

```
User intent
├── Unsure which platform → cli-hub search "<description>"
├── Know platform, not tool → cli-hub list <provider>
├── Found tool ID → cli-hub info <id> → cli-hub run <id> [args]
├── "not installed" → cli-hub install <provider>
├── "not authenticated" → cli-hub auth <provider>
├── "Operation not found" → cli-hub search again
├── "timed out" → cli-hub install <provider> --timeout 300
└── Unsure about env → cli-hub doctor
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `not installed` | CLI not installed | `cli-hub install <provider>` |
| `not authenticated` | Not authenticated | `cli-hub auth <provider>` |
| `Operation not found` | Typo in ID | `cli-hub search` to find correct ID |
| `No adapter registered` | Wrong provider name | `cli-hub list` to see available names |
| `timed out after Ns` | Timeout | Retry with `--timeout 300` |
| `Invalid JSON` | Malformed --args JSON | Check quotes and escaping |
| Underlying CLI error | Wrong params or insufficient permissions | `cli-hub info <id>` to check params |

## Supported Platforms

### Enterprise Collaboration

| Platform | Provider | Tools | Coverage |
|----------|----------|-------|----------|
| WeCom (企业微信) | wecom | 28 | Contacts, Todos, Meetings, Messages, Calendars, Docs, Smart Sheets |
| DingTalk (钉钉) | dingtalk | 23 | Contacts, Groups, Calendar, Todos, Approvals, Attendance, Logs, Smart Sheets |
| Lark/Feishu (飞书) | lark | 28 | Calendar, Messages, Docs, Drive, Bitable, Spreadsheets, Tasks, Wiki, Email, Meetings |
| Google Workspace | gws | 20 | Drive, Gmail, Calendar, Sheets, Docs, Chat, Workflow |

### Developer Tools

| Platform | Provider | Tools | Coverage |
|----------|----------|-------|----------|
| GitHub CLI | gh | 20 | Repos, PRs, Issues, Releases, Actions, Gists, Search, API |
| npm | npm | 16 | Package install/publish/search/audit, Project init/run, Security |
| React Native | react-native | 12 | Create projects, Metro dev server, iOS/Android build & run, Doctor |

### AI Creation

| Platform | Provider | Tools | Coverage |
|----------|----------|-------|----------|
| Dreamina (即梦) | dreamina | 12 | Text-to-Image, Text-to-Video, Image-to-Video, Multimodal Video, Upscale, Seedance 2.0 |

## Notes

- Authentication is interactive; the agent should prompt the user to complete browser authorization
- For Dreamina, use `dreamina login --headless` (terminal QR code); generation consumes credits — warn the user
- Dreamina tasks are async: after submit, use `query_result --submit_id=<id>` to check results
- Search results are ranked by relevance; prefer the highest-scored tool
- Invoke tools one at a time and confirm results before proceeding
- `cli-hub refresh` auto-pulls latest tool schemas from https://clihub.cc — new providers require no cli-hub upgrade
