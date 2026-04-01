"""Tests to verify schema files are correctly located within the package."""

import json
from pathlib import Path

from cli_gateway.core.registry import Registry, _SCHEMAS_DIR


def test_schemas_dir_exists():
    assert _SCHEMAS_DIR.exists(), f"Schema dir not found: {_SCHEMAS_DIR}"
    assert _SCHEMAS_DIR.is_dir()


def test_schemas_dir_inside_package():
    assert "cli_gateway" in str(_SCHEMAS_DIR)
    assert _SCHEMAS_DIR.name == "schemas"


def test_wecom_schema_exists():
    path = _SCHEMAS_DIR / "wecom.json"
    assert path.exists(), f"wecom.json not found at {path}"


def test_dingtalk_schema_exists():
    path = _SCHEMAS_DIR / "dingtalk.json"
    assert path.exists(), f"dingtalk.json not found at {path}"


def test_lark_schema_exists():
    path = _SCHEMAS_DIR / "lark.json"
    assert path.exists(), f"lark.json not found at {path}"


def test_schema_files_valid_json():
    for name in ["wecom.json", "dingtalk.json", "lark.json"]:
        path = _SCHEMAS_DIR / name
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "operations" in data, f"{name} missing 'operations' key"
        assert len(data["operations"]) > 0, f"{name} has empty operations"


def test_schema_operations_have_required_fields():
    required_fields = {"category", "name", "description"}
    for name in ["wecom.json", "dingtalk.json", "lark.json"]:
        path = _SCHEMAS_DIR / name
        data = json.loads(path.read_text(encoding="utf-8"))
        for i, op in enumerate(data["operations"]):
            for field in required_fields:
                assert field in op, f"{name} operation[{i}] missing '{field}'"


def test_registry_loads_all_providers():
    reg = Registry()
    reg.load()
    ops = reg.operations
    providers_found = {op.provider for op in ops}
    assert "wecom" in providers_found
    assert "dingtalk" in providers_found
    assert "lark" in providers_found


def test_registry_operation_count():
    reg = Registry()
    reg.load()
    wecom_count = len(reg.list_operations(provider="wecom"))
    dingtalk_count = len(reg.list_operations(provider="dingtalk"))
    lark_count = len(reg.list_operations(provider="lark"))
    assert wecom_count >= 20, f"Expected ≥20 wecom ops, got {wecom_count}"
    assert dingtalk_count >= 15, f"Expected ≥15 dingtalk ops, got {dingtalk_count}"
    assert lark_count >= 20, f"Expected ≥20 lark ops, got {lark_count}"


def test_registry_total_count():
    reg = Registry()
    reg.load()
    total = len(reg.operations)
    assert total >= 70, f"Expected ≥70 total ops, got {total}"
