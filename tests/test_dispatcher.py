"""Tests for the Dispatcher."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from cli_gateway.adapters.base import AbstractAdapter, InvokeResult
from cli_gateway.core.dispatcher import Dispatcher
from cli_gateway.core.registry import Registry
from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


class MockAdapter(AbstractAdapter):
    def __init__(self, provider: Provider):
        super().__init__(provider)
        self._installed = True

    async def install(self) -> InvokeResult:
        return InvokeResult(success=True, output="installed")

    async def auth(self, profile=None) -> InvokeResult:
        return InvokeResult(success=True)

    async def auth_status(self) -> ProviderStatus:
        return ProviderStatus.AUTHENTICATED

    async def refresh_schema(self) -> list[Operation]:
        return []

    async def invoke(self, operation: Operation, args=None) -> InvokeResult:
        return InvokeResult(success=True, output=f"invoked {operation.id}")

    async def is_installed(self):
        return self._installed, "1.0.0"


def _make_registry():
    reg = Registry.__new__(Registry)
    reg._schemas_dir = None
    reg._providers = {
        "mock": Provider(
            name="mock", display_name="Mock", cli_binary="mock-cli",
            install_command="echo ok",
        )
    }
    reg._operations = [
        Operation(
            id="mock.test.hello", provider="mock", category="test",
            name="hello", description="Say hello",
        )
    ]
    reg._loaded = True
    return reg


def test_dispatcher_invoke_success():
    reg = _make_registry()
    dispatcher = Dispatcher(registry=reg)
    adapter = MockAdapter(reg._providers["mock"])
    dispatcher.register_adapter("mock", adapter)

    result = asyncio.run(dispatcher.invoke("mock.test.hello"))
    assert result.success
    assert "invoked mock.test.hello" in result.output


def test_dispatcher_operation_not_found():
    reg = _make_registry()
    dispatcher = Dispatcher(registry=reg)

    result = asyncio.run(dispatcher.invoke("nonexistent.op"))
    assert not result.success
    assert "not found" in result.error


def test_dispatcher_no_adapter():
    reg = _make_registry()
    dispatcher = Dispatcher(registry=reg)

    result = asyncio.run(dispatcher.invoke("mock.test.hello"))
    assert not result.success
    assert "No adapter" in result.error


def test_dispatcher_not_installed():
    reg = _make_registry()
    dispatcher = Dispatcher(registry=reg)
    adapter = MockAdapter(reg._providers["mock"])
    adapter._installed = False
    dispatcher.register_adapter("mock", adapter)

    result = asyncio.run(dispatcher.invoke("mock.test.hello"))
    assert not result.success
    assert "not installed" in result.error
