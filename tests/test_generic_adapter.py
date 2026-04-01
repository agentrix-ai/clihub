"""Tests for the GenericAdapter."""

import asyncio
import json

from cli_gateway.adapters.generic import GenericAdapter, InvokeStyle
from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


def _provider(schema_cmd: str = "", status_cmd: str = ""):
    return Provider(
        name="test", display_name="Test", cli_binary="echo",
        install_command="echo installed",
        auth_commands=["echo authed"],
        schema_command=schema_cmd,
        status_command=status_cmd,
    )


def _op(argv: list[str] | None = None):
    return Operation(
        id="test.cat.do_thing", provider="test", category="cat", name="do_thing",
        description="Test op", argv_template=argv or [],
    )


# ── invoke style: flags ──

def test_flags_invoke_with_args():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.FLAGS)
    op = _op(["echo", "cat", "do_thing"])
    result = asyncio.run(adapter.invoke(op, {"key": "value", "num": 42}))
    assert "--key" in result.raw_command
    assert "--num" in result.raw_command


def test_flags_invoke_dict_arg_quoted():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.FLAGS)
    op = _op(["echo", "test"])
    result = asyncio.run(adapter.invoke(op, {"data": {"nested": True}}))
    assert "--data" in result.raw_command


def test_flags_invoke_bool_true():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.FLAGS)
    op = _op(["echo", "test"])
    result = asyncio.run(adapter.invoke(op, {"verbose": True}))
    assert "--verbose" in result.raw_command


def test_flags_invoke_bool_false_excluded():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.FLAGS)
    op = _op(["echo", "test"])
    result = asyncio.run(adapter.invoke(op, {"verbose": False}))
    assert "--verbose" not in result.raw_command


def test_flags_invoke_no_args():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.FLAGS)
    op = _op(["echo", "cat", "do_thing"])
    result = asyncio.run(adapter.invoke(op))
    assert result.raw_command == "echo cat do_thing"


# ── invoke style: json_arg ──

def test_json_arg_invoke():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.JSON_ARG)
    op = _op(["echo", "test", "cmd"])
    result = asyncio.run(adapter.invoke(op, {"key": "value"}))
    assert "echo test cmd" in result.raw_command


def test_json_arg_invoke_no_args():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.JSON_ARG)
    op = _op(["echo", "test"])
    result = asyncio.run(adapter.invoke(op))
    assert result.raw_command == "echo test"


# ── fallback argv ──

def test_invoke_without_argv_template():
    adapter = GenericAdapter(_provider(), invoke_style=InvokeStyle.FLAGS)
    op = _op()
    result = asyncio.run(adapter.invoke(op, {"x": "1"}))
    assert "echo" in result.raw_command
    assert "cat" in result.raw_command
    assert "do_thing" in result.raw_command


# ── install / auth ──

def test_install():
    adapter = GenericAdapter(_provider())
    result = asyncio.run(adapter.install())
    assert result.success


def test_auth():
    adapter = GenericAdapter(_provider())
    result = asyncio.run(adapter.auth())
    assert result.success


def test_auth_no_commands():
    prov = Provider(
        name="noauth", display_name="NoAuth", cli_binary="echo",
        install_command="echo ok", auth_commands=[],
    )
    adapter = GenericAdapter(prov)
    result = asyncio.run(adapter.auth())
    assert not result.success
    assert "No auth commands" in result.error


# ── auth_status ──

def test_auth_status_installed():
    adapter = GenericAdapter(_provider(status_cmd="echo ok"))
    status = asyncio.run(adapter.auth_status())
    assert status == ProviderStatus.AUTHENTICATED


def test_auth_status_no_status_cmd():
    adapter = GenericAdapter(_provider())
    status = asyncio.run(adapter.auth_status())
    assert status == ProviderStatus.INSTALLED


# ── refresh_schema ──

def test_refresh_schema_no_command():
    adapter = GenericAdapter(_provider())
    ops = asyncio.run(adapter.refresh_schema())
    assert ops == []


def test_parse_schema_json():
    adapter = GenericAdapter(_provider())
    data = {
        "products": [{
            "id": "calendar",
            "tools": [
                {"name": "create", "description": "Create event"},
                {"name": "list", "description": "List events"},
            ],
        }],
    }
    ops = adapter._parse_schema_json(data)
    assert len(ops) == 2
    assert ops[0].id == "test.calendar.create"
    assert ops[1].category == "calendar"
