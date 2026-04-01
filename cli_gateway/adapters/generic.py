"""Generic adapter — works for any CLI that follows common patterns.

Covers two invoke styles:
  - JSON arg:  <binary> <category> <method> '<json>'   (wecom-style)
  - Flag args: <binary> <category> <method> --key val   (dingtalk/lark-style)

New providers can use this adapter without writing custom code.
"""

from __future__ import annotations

import json
import shlex

from cli_gateway.adapters.base import AbstractAdapter, InvokeResult
from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


class InvokeStyle:
    JSON_ARG = "json_arg"
    FLAGS = "flags"


class GenericAdapter(AbstractAdapter):
    """Adapter that works for any CLI by configuration alone."""

    def __init__(self, provider: Provider, invoke_style: str = InvokeStyle.FLAGS) -> None:
        super().__init__(provider)
        self._invoke_style = invoke_style

    async def install(self) -> InvokeResult:
        return await self._run_shell(self.provider.install_command, timeout=300)

    async def auth(self, profile: str | None = None) -> InvokeResult:
        if not self.provider.auth_commands:
            return InvokeResult(success=False, error="No auth commands configured")
        last = InvokeResult(success=True)
        for cmd in self.provider.auth_commands:
            last = await self._run_shell(cmd, timeout=120)
            if not last.success:
                return last
        return last

    async def auth_status(self) -> ProviderStatus:
        installed, _ = await self.is_installed()
        if not installed:
            return ProviderStatus.NOT_INSTALLED
        if self.provider.status_command:
            result = await self._run_shell(self.provider.status_command, timeout=15)
            if result.success:
                return ProviderStatus.AUTHENTICATED
        return ProviderStatus.INSTALLED

    async def refresh_schema(self) -> list[Operation]:
        if not self.provider.schema_command:
            return []
        result = await self._run_shell(self.provider.schema_command, timeout=30)
        if not result.success or not result.output:
            return []
        try:
            data = json.loads(result.output)
        except json.JSONDecodeError:
            return []
        return self._parse_schema_json(data)

    def _parse_schema_json(self, data: dict) -> list[Operation]:
        """Parse common schema JSON structures into Operations."""
        ops: list[Operation] = []
        products = data.get("products", data.get("services", data.get("commands", [])))
        for product in products:
            pid = product.get("id", product.get("name", ""))
            tools = product.get("tools", product.get("commands", []))
            for tool in tools:
                tname = tool.get("name", tool.get("id", ""))
                ops.append(Operation(
                    id=f"{self.provider.name}.{pid}.{tname}",
                    provider=self.provider.name,
                    category=pid,
                    name=tname,
                    description=tool.get("description", ""),
                    description_en=tool.get("description_en", ""),
                    keywords=[pid, tname],
                    argv_template=tool.get("argv", []),
                    input_schema=tool.get("parameters"),
                ))
        return ops

    async def invoke(self, operation: Operation, args: dict | None = None) -> InvokeResult:
        if operation.argv_template:
            argv = list(operation.argv_template)
        else:
            argv = [self.provider.cli_binary, operation.category, operation.name]

        if args:
            if self._invoke_style == InvokeStyle.JSON_ARG:
                argv.append(shlex.quote(json.dumps(args, ensure_ascii=False)))
            else:
                for key, value in args.items():
                    argv.append(f"--{key}")
                    if isinstance(value, (dict, list)):
                        argv.append(shlex.quote(json.dumps(value, ensure_ascii=False)))
                    elif isinstance(value, bool):
                        if not value:
                            argv.pop()  # remove the --key if false
                    else:
                        argv.append(shlex.quote(str(value)))

        cmd = " ".join(argv)
        return await self._run_shell(cmd)
