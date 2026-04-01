"""Unified Schema Registry — loads, caches and queries Operations from all providers."""

from __future__ import annotations

import json
from pathlib import Path

from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

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
        """Load all static schemas from JSON files."""
        self._operations.clear()
        for name in self._providers:
            schema_file = self._schemas_dir / f"{name}.json"
            if schema_file.exists():
                self._load_schema_file(name, schema_file)
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
