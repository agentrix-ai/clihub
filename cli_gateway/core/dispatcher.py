"""Dispatcher — routes operation calls to the correct adapter."""

from __future__ import annotations

from cli_gateway.adapters.base import AbstractAdapter, InvokeResult
from cli_gateway.core.registry import Registry, get_registry
from cli_gateway.models.operation import Operation


class Dispatcher:
    """Route an operation_id to the right adapter, build argv, and execute."""

    def __init__(self, registry: Registry | None = None) -> None:
        self._registry = registry or get_registry()
        self._adapters: dict[str, AbstractAdapter] = {}

    def register_adapter(self, provider_name: str, adapter: AbstractAdapter) -> None:
        self._adapters[provider_name] = adapter

    def get_adapter(self, provider_name: str) -> AbstractAdapter | None:
        return self._adapters.get(provider_name)

    async def invoke(
        self, operation_id: str, args: dict | None = None
    ) -> InvokeResult:
        op = self._registry.get_operation(operation_id)
        if op is None:
            return InvokeResult(
                success=False,
                error=f"Operation not found: {operation_id}",
                exit_code=1,
            )

        adapter = self._adapters.get(op.provider)
        if adapter is None:
            return InvokeResult(
                success=False,
                error=f"No adapter registered for provider: {op.provider}",
                exit_code=1,
            )

        installed, _ = await adapter.is_installed()
        if not installed:
            return InvokeResult(
                success=False,
                error=f"CLI not installed for {op.provider}. Run: cli-hub install {op.provider}",
                exit_code=1,
            )

        return await adapter.invoke(op, args)

    async def invoke_operation(
        self, operation: Operation, args: dict | None = None
    ) -> InvokeResult:
        adapter = self._adapters.get(operation.provider)
        if adapter is None:
            return InvokeResult(
                success=False,
                error=f"No adapter registered for provider: {operation.provider}",
                exit_code=1,
            )
        return await adapter.invoke(operation, args)
