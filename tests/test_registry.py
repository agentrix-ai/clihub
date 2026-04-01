"""Tests for the Schema Registry."""

from pathlib import Path

from cli_gateway.core.registry import Registry, BUILTIN_PROVIDERS


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "cli_gateway" / "schemas"


def test_builtin_providers():
    assert "wecom" in BUILTIN_PROVIDERS
    assert "dingtalk" in BUILTIN_PROVIDERS
    assert "lark" in BUILTIN_PROVIDERS
    assert "gws" in BUILTIN_PROVIDERS
    assert "gh" in BUILTIN_PROVIDERS
    assert "npm" in BUILTIN_PROVIDERS
    assert "react-native" in BUILTIN_PROVIDERS


def test_registry_load():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    reg.load()
    assert len(reg.operations) > 0


def test_registry_providers():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    providers = reg.providers
    assert "wecom" in providers
    assert "dingtalk" in providers
    assert "lark" in providers
    assert "gws" in providers
    assert "gh" in providers
    assert "npm" in providers
    assert "react-native" in providers


def test_get_operation_by_id():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    op = reg.get_operation("lark.calendar.agenda")
    assert op is not None
    assert op.provider == "lark"
    assert op.category == "calendar"


def test_list_operations_by_provider():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    wecom_ops = reg.list_operations(provider="wecom")
    assert len(wecom_ops) > 0
    assert all(op.provider == "wecom" for op in wecom_ops)


def test_list_operations_by_category():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    todo_ops = reg.list_operations(category="todo")
    assert len(todo_ops) > 0
    assert all(op.category == "todo" for op in todo_ops)


def test_get_categories():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    cats = reg.get_categories()
    assert "calendar" in cats or "todo" in cats


def test_get_categories_by_provider():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    cats = reg.get_categories(provider="lark")
    assert "calendar" in cats
    assert "im" in cats


def test_operation_not_found():
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    op = reg.get_operation("nonexistent.foo.bar")
    assert op is None


def test_register_new_provider():
    from cli_gateway.models.provider import Provider
    reg = Registry(schemas_dir=SCHEMAS_DIR)
    new_prov = Provider(
        name="test_provider",
        display_name="Test",
        cli_binary="test-cli",
        install_command="echo install",
    )
    reg.register_provider(new_prov)
    assert reg.get_provider("test_provider") is not None
