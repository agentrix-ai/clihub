"""Tests for adapter implementations."""

import asyncio
import json

from cli_gateway.adapters.wecom import WeComAdapter
from cli_gateway.adapters.dingtalk import DingTalkAdapter
from cli_gateway.adapters.lark import LarkAdapter
from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider


def _wecom_provider():
    return Provider(
        name="wecom", display_name="WeCom", cli_binary="wecom-cli",
        install_command="echo install", auth_commands=["echo auth"],
    )


def _dingtalk_provider():
    return Provider(
        name="dingtalk", display_name="DingTalk", cli_binary="dws",
        install_command="echo install", auth_commands=["echo auth"],
        schema_command="echo '{}'",
    )


def _lark_provider():
    return Provider(
        name="lark", display_name="Lark", cli_binary="lark-cli",
        install_command="echo install", auth_commands=["echo auth"],
        schema_command="echo '{}'",
    )


def _sample_op(provider: str, argv: list[str] | None = None):
    return Operation(
        id=f"{provider}.test.op",
        provider=provider, category="test", name="op",
        description="Test operation",
        argv_template=argv or [],
    )


def test_wecom_adapter_creation():
    adapter = WeComAdapter(_wecom_provider())
    assert adapter.provider.name == "wecom"


def test_dingtalk_adapter_creation():
    adapter = DingTalkAdapter(_dingtalk_provider())
    assert adapter.provider.name == "dingtalk"


def test_lark_adapter_creation():
    adapter = LarkAdapter(_lark_provider())
    assert adapter.provider.name == "lark"


def test_wecom_invoke_builds_command():
    adapter = WeComAdapter(_wecom_provider())
    op = _sample_op("wecom", ["wecom-cli", "todo", "create_todo"])
    result = asyncio.run(adapter.invoke(op, {"content": "test"}))
    assert "wecom-cli" in result.raw_command


def test_dingtalk_invoke_adds_yes_flag():
    adapter = DingTalkAdapter(_dingtalk_provider())
    op = _sample_op("dingtalk", ["dws", "todo", "task", "create"])
    result = asyncio.run(adapter.invoke(op, {"title": "test"}))
    assert "--yes" in result.raw_command


def test_lark_invoke_with_dict_args():
    adapter = LarkAdapter(_lark_provider())
    op = _sample_op("lark", ["lark-cli", "base", "+record-create"])
    result = asyncio.run(adapter.invoke(op, {"fields": {"Name": "value"}}))
    assert "--fields" in result.raw_command


def test_wecom_invoke_without_argv_template():
    adapter = WeComAdapter(_wecom_provider())
    op = _sample_op("wecom")
    op.argv_template = []
    result = asyncio.run(adapter.invoke(op, {"content": "hello"}))
    assert "wecom-cli" in result.raw_command
    assert "test" in result.raw_command


def test_dingtalk_refresh_schema_empty():
    adapter = DingTalkAdapter(_dingtalk_provider())
    result = asyncio.run(adapter.refresh_schema())
    assert isinstance(result, list)


def test_lark_refresh_schema_empty():
    adapter = LarkAdapter(_lark_provider())
    result = asyncio.run(adapter.refresh_schema())
    assert isinstance(result, list)
