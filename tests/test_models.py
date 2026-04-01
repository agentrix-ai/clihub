"""Tests for data models."""

from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


# ── Operation ────────────────────────────────────────────

def test_operation_search_text():
    op = Operation(
        id="lark.im.send", provider="lark", category="im", name="send",
        description="发送消息", description_en="Send message",
        keywords=["消息", "chat"],
    )
    text = op.search_text
    assert "lark.im.send" in text
    assert "发送消息" in text
    assert "Send message" in text
    assert "消息" in text
    assert "chat" in text


def test_operation_search_text_no_keywords():
    op = Operation(
        id="test.a.b", provider="test", category="a", name="b",
        description="desc",
    )
    text = op.search_text
    assert "test.a.b" in text
    assert "desc" in text


def test_operation_defaults():
    op = Operation(id="t.a.b", provider="t", category="a", name="b")
    assert op.description == ""
    assert op.keywords == []
    assert op.argv_template == []
    assert op.input_schema is None
    assert op.example == ""
    assert op.auth_required is True


def test_operation_with_schema():
    schema = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}
    op = Operation(
        id="t.a.b", provider="t", category="a", name="b",
        input_schema=schema,
    )
    assert op.input_schema is not None
    assert "x" in op.input_schema["properties"]


# ── Provider ─────────────────────────────────────────────

def test_provider_defaults():
    prov = Provider(name="test", cli_binary="test-cli", install_command="echo ok")
    assert prov.display_name == ""
    assert prov.auth_commands == []
    assert prov.version_flag == "--version"
    assert prov.homepage == ""


def test_provider_status_enum():
    assert ProviderStatus.NOT_INSTALLED == "not_installed"
    assert ProviderStatus.INSTALLED == "installed"
    assert ProviderStatus.AUTHENTICATED == "authenticated"
