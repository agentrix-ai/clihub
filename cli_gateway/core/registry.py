"""Unified Schema Registry — loads, caches and queries Operations from all providers."""

from __future__ import annotations

import json
from pathlib import Path

from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_LOCAL_CACHE_DIR = Path.home() / ".cli-hub" / "schemas"
REMOTE_REGISTRY_URL = "https://clihub.cc/api/schemas"

# Built-in provider definitions (data-driven, easily extensible)
BUILTIN_PROVIDERS: dict[str, Provider] = {
    "wecom": Provider(
        name="wecom",
        display_name="WeCom (企业微信)",
        cli_binary="wecom-cli",
        install_command="npm install -g @wecom/cli && npx skills add WeComTeam/wecom-cli -y -g",
        auth_commands=["wecom-cli init"],
        status_command="wecom-cli --version",
        schema_command="",
        homepage="https://github.com/WecomTeam/wecom-cli",
        description="企业微信 CLI — 通讯录、待办、会议、消息、日程、文档、智能表格",
    ),
    "dingtalk": Provider(
        name="dingtalk",
        display_name="DingTalk (钉钉)",
        cli_binary="dws",
        install_command="curl -fsSL https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.sh | sh",
        auth_commands=["dws auth login"],
        status_command="dws auth status",
        schema_command="dws schema",
        homepage="https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli",
        description="钉钉 CLI — 通讯录、群聊、日历、待办、审批、考勤、日志、智能表格",
    ),
    "lark": Provider(
        name="lark",
        display_name="Lark / Feishu (飞书)",
        cli_binary="lark-cli",
        install_command="npm install -g @larksuite/cli && npx skills add larksuite/cli -y -g",
        auth_commands=["lark-cli config init --new", "lark-cli auth login --recommend"],
        status_command="lark-cli auth status",
        schema_command="lark-cli schema",
        homepage="https://github.com/larksuite/cli",
        description="飞书 CLI — 日历、消息、文档、云盘、多维表格、电子表格、任务、Wiki、邮件、会议",
    ),
    "dreamina": Provider(
        name="dreamina",
        display_name="Dreamina (即梦)",
        cli_binary="dreamina",
        install_command="curl -s https://jimeng.jianying.com/cli | bash",
        auth_commands=["dreamina login --headless"],
        status_command="dreamina user_credit",
        schema_command="",
        homepage="https://jimeng.jianying.com",
        description="即梦 CLI — AI 文生图、文生视频、图生视频、多模态视频、图片超分、Seedance 2.0",
    ),
    "gws": Provider(
        name="gws",
        display_name="Google Workspace (GWS)",
        cli_binary="gws",
        install_command="npm install -g @googleworkspace/cli",
        auth_commands=["gws auth setup", "gws auth login"],
        status_command="gws auth login --scopes drive",
        schema_command="",
        homepage="https://github.com/googleworkspace/cli",
        description="Google Workspace CLI — Drive、Gmail、Calendar、Sheets、Docs、Chat、Admin 全覆盖，动态发现 API",
    ),
    "gh": Provider(
        name="gh",
        display_name="GitHub CLI (gh)",
        cli_binary="gh",
        install_command="brew install gh || (curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && echo 'deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main' | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt update && sudo apt install gh -y)",
        auth_commands=["gh auth login"],
        status_command="gh auth status",
        schema_command="",
        homepage="https://github.com/cli/cli",
        description="GitHub CLI — 仓库、PR、Issue、Release、Actions、Gist、搜索，命令行操作 GitHub",
    ),
    "npm": Provider(
        name="npm",
        display_name="npm",
        cli_binary="npm",
        install_command="echo 'npm is bundled with Node.js. Install Node.js from https://nodejs.org'",
        auth_commands=["npm login"],
        status_command="npm whoami",
        schema_command="",
        homepage="https://github.com/npm/cli",
        description="npm — JavaScript 包管理器，安装/发布/搜索/审计 npm 包",
    ),
    "react-native": Provider(
        name="react-native",
        display_name="React Native CLI",
        cli_binary="npx",
        install_command="npm install -g @react-native-community/cli",
        auth_commands=[],
        status_command="npx react-native --version",
        schema_command="",
        version_flag="react-native --version",
        homepage="https://github.com/react-native-community/cli",
        description="React Native CLI — 创建、构建、运行 React Native 应用（iOS/Android）",
    ),
}


class Registry:
    """Central registry holding all providers and their operations."""

    def __init__(self, schemas_dir: Path | None = None) -> None:
        self._schemas_dir = schemas_dir or _SCHEMAS_DIR
        self._providers: dict[str, Provider] = dict(BUILTIN_PROVIDERS)
        self._operations: list[Operation] = []
        self._loaded = False

    # ── public API ───────────────────────────────────────

    @property
    def providers(self) -> dict[str, Provider]:
        return dict(self._providers)

    @property
    def operations(self) -> list[Operation]:
        if not self._loaded:
            self.load()
        return list(self._operations)

    def load(self) -> None:
        """Load schemas: local cache (~/.cli-hub/schemas/) > built-in package schemas."""
        self._operations.clear()
        loaded_providers: set[str] = set()

        # Priority 1: local cache (populated by `cli-hub refresh`)
        if _LOCAL_CACHE_DIR.exists():
            for f in _LOCAL_CACHE_DIR.glob("*.json"):
                if f.stem in self._providers or f.stem not in loaded_providers:
                    self._load_schema_file(f.stem, f)
                    loaded_providers.add(f.stem)

        # Priority 2: built-in schemas (fallback for providers not in cache)
        for name in self._providers:
            if name not in loaded_providers:
                schema_file = self._schemas_dir / f"{name}.json"
                if schema_file.exists():
                    self._load_schema_file(name, schema_file)
                    loaded_providers.add(name)

        self._loaded = True

    def get_provider(self, name: str) -> Provider | None:
        return self._providers.get(name)

    def get_operation(self, operation_id: str) -> Operation | None:
        if not self._loaded:
            self.load()
        for op in self._operations:
            if op.id == operation_id:
                return op
        return None

    def list_operations(
        self,
        provider: str | None = None,
        category: str | None = None,
    ) -> list[Operation]:
        if not self._loaded:
            self.load()
        ops = self._operations
        if provider:
            ops = [o for o in ops if o.provider == provider]
        if category:
            ops = [o for o in ops if o.category == category]
        return ops

    def get_categories(self, provider: str | None = None) -> list[str]:
        ops = self.list_operations(provider=provider)
        return sorted({o.category for o in ops})

    def add_operations(self, ops: list[Operation]) -> None:
        existing_ids = {o.id for o in self._operations}
        for op in ops:
            if op.id not in existing_ids:
                self._operations.append(op)
                existing_ids.add(op.id)

    def register_provider(self, provider: Provider) -> None:
        """Register a new provider (for dynamic expansion)."""
        self._providers[provider.name] = provider

    # ── internal ─────────────────────────────────────────

    def _load_schema_file(self, provider_name: str, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        operations_data = data.get("operations", [])
        for item in operations_data:
            item.setdefault("provider", provider_name)
            if "id" not in item:
                item["id"] = f"{provider_name}.{item.get('category','')}.{item.get('name','')}"
            try:
                self._operations.append(Operation.model_validate(item))
            except Exception:
                continue


# Module-level singleton
_registry: Registry | None = None


def get_registry() -> Registry:
    global _registry
    if _registry is None:
        _registry = Registry()
    return _registry
