"""Lark / Feishu (飞书) CLI adapter.

Three-layer command system:
  - Shortcuts: lark-cli <service> +<shortcut> [--flags]
  - API Commands: lark-cli <service> <resource> <action> [--params JSON]
  - Raw API: lark-cli api <METHOD> <path> [--body JSON]

Supports: lark-cli schema for dynamic schema discovery.
"""

from __future__ import annotations

import json
import shlex

from cli_gateway.adapters.base import AbstractAdapter, InvokeResult
from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


class LarkAdapter(AbstractAdapter):

    def __init__(self, provider: Provider) -> None:
        super().__init__(provider)

    async def install(self) -> InvokeResult:
        return await self._run_shell(self.provider.install_command, timeout=300)

    async def auth(self, profile: str | None = None) -> InvokeResult:
        if not self.provider.auth_commands:
            return InvokeResult(success=False, error="No auth commands configured")
        last_result = InvokeResult(success=True)
        for cmd in self.provider.auth_commands:
            last_result = await self._run_shell(cmd, timeout=120)
            if not last_result.success:
                return last_result
        return last_result

    async def auth_status(self) -> ProviderStatus:
        installed, _ = await self.is_installed()
        if not installed:
            return ProviderStatus.NOT_INSTALLED
        if self.provider.status_command:
            result = await self._run_shell(self.provider.status_command, timeout=15)
            if result.success:
                output_lower = result.output.lower()
                if "logged in" in output_lower or "authenticated" in output_lower:
                    return ProviderStatus.AUTHENTICATED
        return ProviderStatus.INSTALLED

    async def refresh_schema(self) -> list[Operation]:
        """Fetch schema from `lark-cli schema` and parse into Operations."""
        if not self.provider.schema_command:
            return []

        result = await self._run_shell(self.provider.schema_command, timeout=30)
        if not result.success or not result.output:
            return []

        try:
            data = json.loads(result.output)
        except json.JSONDecodeError:
            return []

        ops: list[Operation] = []
        products = data.get("products", data.get("services", []))
        for product in products:
            product_id = product.get("id", product.get("name", ""))
            tools = product.get("tools", product.get("commands", []))
            for tool in tools:
                tool_name = tool.get("name", tool.get("id", ""))
                op = Operation(
                    id=f"lark.{product_id}.{tool_name}",
                    provider="lark",
                    category=product_id,
                    name=tool_name,
                    description=tool.get("description", ""),
                    description_en=tool.get("description_en", tool.get("description", "")),
                    keywords=[product_id, tool_name],
                    argv_template=tool.get("argv", []),
                    input_schema=tool.get("parameters"),
                )
                ops.append(op)
        return ops

    async def invoke(self, operation: Operation, args: dict | None = None) -> InvokeResult:
        if operation.argv_template:
            argv = list(operation.argv_template)
        else:
            argv = [self.provider.cli_binary, operation.category, operation.name]

        if args:
            for key, value in args.items():
                argv.append(f"--{key}")
                if isinstance(value, (dict, list)):
                    argv.append(shlex.quote(json.dumps(value, ensure_ascii=False)))
                else:
                    argv.append(shlex.quote(str(value)))

        cmd = " ".join(argv)
        return await self._run_shell(cmd)
