"""WeCom (企业微信) CLI adapter.

Command pattern: wecom-cli <category> <method> [json_args]
No schema command available — relies on static schema.
"""

from __future__ import annotations

import json
import shlex

from cli_gateway.adapters.base import AbstractAdapter, InvokeResult
from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


class WeComAdapter(AbstractAdapter):

    def __init__(self, provider: Provider) -> None:
        super().__init__(provider)

    async def install(self) -> InvokeResult:
        return await self._run_shell(self.provider.install_command, timeout=300)

    async def auth(self, profile: str | None = None) -> InvokeResult:
        if not self.provider.auth_commands:
            return InvokeResult(success=False, error="No auth commands configured")
        cmd = self.provider.auth_commands[0]
        return await self._run_shell(cmd)

    async def auth_status(self) -> ProviderStatus:
        installed, _ = await self.is_installed()
        if not installed:
            return ProviderStatus.NOT_INSTALLED
        return ProviderStatus.INSTALLED

    async def refresh_schema(self) -> list[Operation]:
        return []

    async def invoke(self, operation: Operation, args: dict | None = None) -> InvokeResult:
        if operation.argv_template:
            argv = list(operation.argv_template)
        else:
            argv = [self.provider.cli_binary, operation.category, operation.name]

        if args:
            argv.append(shlex.quote(json.dumps(args, ensure_ascii=False)))

        cmd = " ".join(argv)
        return await self._run_shell(cmd)
