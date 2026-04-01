---
name: cli-hub-integration-sop
description: "cli-hub 新 CLI 集成标准流程（SOP）。当用户要求集成新的 CLI 工具到 cli-hub 时使用此 Skill。"
---

# cli-hub 新 CLI 集成 SOP

将一个新的 CLI 工具集成到 cli-hub 的标准化流程。按步骤执行即可。

## 前提

- cli-hub 工程路径：`/Users/xiexinfa/cli-gateway-py`
- 已安装 `uv`，使用 `uv run` 执行测试

## Step 1: 信息收集

对目标 CLI 收集以下信息（从 GitHub README / 官网获取）：

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 短标识符（英文，小写，无空格） | `gws` |
| `display_name` | 展示名 | `Google Workspace (GWS)` |
| `cli_binary` | PATH 上的二进制名 | `gws` |
| `install_command` | 一键安装命令 | `npm install -g @googleworkspace/cli` |
| `auth_commands` | 认证命令列表 | `["gws auth setup", "gws auth login"]` |
| `status_command` | 检查认证状态的命令 | `gws auth status` |
| `schema_command` | 动态 schema 命令（如有） | `""` |
| `version_flag` | 版本检查参数（默认 `--version`） | `--version` |
| `homepage` | 项目主页 | `https://github.com/googleworkspace/cli` |
| `description` | 一句话描述 | `Google Workspace CLI — Drive、Gmail、Calendar...` |

同时梳理出该 CLI 的**核心操作列表**（10-20 个最常用的命令），包括：
- 命令的 category（功能分类）
- 命令名称 name
- 中英文描述
- 调用模板 argv_template
- 参数 schema（如有）
- 示例命令

## Step 2: 创建 Schema JSON

在 `cli_gateway/schemas/{name}.json` 创建 schema 文件：

```json
{
  "provider": "{name}",
  "version": "1.0.0",
  "operations": [
    {
      "category": "分类",
      "name": "操作名",
      "description": "中文描述",
      "description_en": "English description",
      "keywords": ["关键词1", "keyword2"],
      "argv_template": ["binary", "subcommand", "action"],
      "input_schema": {
        "type": "object",
        "properties": {
          "param1": {"type": "string", "description": "参数描述"}
        },
        "required": ["param1"]
      },
      "example": "binary subcommand action --param1 value",
      "auth_required": true
    }
  ]
}
```

**schema 编写规范：**
- `id` 字段不用写，Registry 自动生成为 `{provider}.{category}.{name}`
- `keywords` 包含中英文关键词，提升搜索命中率
- `argv_template` 是实际执行的命令数组
- `input_schema` 遵循 JSON Schema 格式
- `auth_required` 默认 true，纯本地命令设为 false
- 无参数的命令可省略 `input_schema`

## Step 3: 注册 Provider

编辑 `cli_gateway/core/registry.py`，在 `BUILTIN_PROVIDERS` 字典中添加：

```python
"{name}": Provider(
    name="{name}",
    display_name="{display_name}",
    cli_binary="{cli_binary}",
    install_command="{install_command}",
    auth_commands=["{auth_cmd1}", "{auth_cmd2}"],
    status_command="{status_command}",
    schema_command="",
    homepage="{homepage}",
    description="{description}",
),
```

## Step 4: 同步到 Website

```bash
cp cli_gateway/schemas/{name}.json website/schemas/{name}.json
```

编辑 `website/schemas/providers.json`，追加 provider 元数据对象。

## Step 5: 添加测试

在 `tests/test_schema_path.py` 中添加：

```python
def test_{name}_schema_exists():
    path = _SCHEMAS_DIR / "{name}.json"
    assert path.exists(), f"{name}.json not found at {path}"
```

在 `ALL_SCHEMAS` 列表中追加 `"{name}.json"`。

在 `tests/test_registry.py` 的 `test_builtin_providers` 和 `test_registry_providers` 中追加：
```python
assert "{name}" in BUILTIN_PROVIDERS
```

更新 `test_registry_total_count` 中的最低总数阈值。

## Step 6: 运行测试

```bash
cd /Users/xiexinfa/cli-gateway-py
uv run python -m pytest tests/ -v --tb=short
```

确保全部通过。

## Step 7: 更新文档

### SKILL.md / SKILL_EN.md

在 provider 列表中追加新 CLI，更新工具总数。

### claude.md

如有架构变化，更新工程指南。

### website/templates/index.html

landing page 的 provider 列表是动态渲染的（从 schemas 读取），无需手动修改。

## Step 8: 部署

```bash
cd /Users/xiexinfa/cli-gateway-py/website
bash deploy.sh deploy
```

部署后验证：
```bash
curl -s https://clihub.cc/api/providers | python3 -m json.tool
curl -s https://clihub.cc/api/schemas/{name} | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"operations\"])} ops')"
```

## Checklist

- [ ] Schema JSON 创建（`cli_gateway/schemas/{name}.json`）
- [ ] Provider 注册（`registry.py` BUILTIN_PROVIDERS）
- [ ] Website schema 同步（`website/schemas/`）
- [ ] providers.json 更新
- [ ] 测试用例添加
- [ ] 测试全部通过
- [ ] SKILL.md 更新
- [ ] 部署到 clihub.cc

## 常见问题

**Q: CLI 的命令格式不是 `binary subcmd action --flag val` 怎么办？**
A: 在 `argv_template` 中完整写出命令前缀。GenericAdapter 会使用 argv_template + 追加 flag 参数的方式调用。

**Q: CLI 需要自定义 Adapter 吗？**
A: 99% 的 CLI 用 GenericAdapter 就够了。只有当 CLI 有特殊的 schema 解析逻辑（如 dingtalk 的 `dws schema`）或特殊的调用模式时才需要自定义 Adapter。

**Q: 如何处理需要 npx 而非全局安装的 CLI？**
A: `cli_binary` 设为 `npx`，`argv_template` 中写完整命令如 `["npx", "react-native", "start"]`，`version_flag` 设为 `react-native --version`。

**Q: install_command 很长怎么办？**
A: 使用 `||` 链接多种安装方式（brew 优先，apt 兜底），或直接写 `echo '...'` 提示用户手动安装。
