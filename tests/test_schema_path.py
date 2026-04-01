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


def test_dreamina_schema_exists():
    path = _SCHEMAS_DIR / "dreamina.json"
    assert path.exists(), f"dreamina.json not found at {path}"


def test_gws_schema_exists():
    path = _SCHEMAS_DIR / "gws.json"
    assert path.exists(), f"gws.json not found at {path}"


def test_gh_schema_exists():
    path = _SCHEMAS_DIR / "gh.json"
    assert path.exists(), f"gh.json not found at {path}"


def test_npm_schema_exists():
    path = _SCHEMAS_DIR / "npm.json"
    assert path.exists(), f"npm.json not found at {path}"


def test_react_native_schema_exists():
    path = _SCHEMAS_DIR / "react-native.json"
    assert path.exists(), f"react-native.json not found at {path}"


ALL_SCHEMAS = ["wecom.json", "dingtalk.json", "lark.json", "dreamina.json",
               "gws.json", "gh.json", "npm.json", "react-native.json"]


def test_schema_files_valid_json():
    for name in ALL_SCHEMAS:
        path = _SCHEMAS_DIR / name
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "operations" in data, f"{name} missing 'operations' key"
        assert len(data["operations"]) > 0, f"{name} has empty operations"


def test_schema_operations_have_required_fields():
    required_fields = {"category", "name", "description"}
    for name in ALL_SCHEMAS:
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
    assert "dreamina" in providers_found
    assert "gws" in providers_found
    assert "gh" in providers_found
    assert "npm" in providers_found
    assert "react-native" in providers_found


def test_registry_operation_count():
    reg = Registry()
    reg.load()
    wecom_count = len(reg.list_operations(provider="wecom"))
    dingtalk_count = len(reg.list_operations(provider="dingtalk"))
    lark_count = len(reg.list_operations(provider="lark"))
    assert wecom_count >= 20, f"Expected ≥20 wecom ops, got {wecom_count}"
    assert dingtalk_count >= 15, f"Expected ≥15 dingtalk ops, got {dingtalk_count}"
    assert lark_count >= 20, f"Expected ≥20 lark ops, got {lark_count}"


def test_dreamina_operation_count():
    reg = Registry()
    reg.load()
    dreamina_count = len(reg.list_operations(provider="dreamina"))
    assert dreamina_count >= 10, f"Expected ≥10 dreamina ops, got {dreamina_count}"


def test_new_providers_operation_count():
    reg = Registry()
    reg.load()
    gws_count = len(reg.list_operations(provider="gws"))
    gh_count = len(reg.list_operations(provider="gh"))
    npm_count = len(reg.list_operations(provider="npm"))
    rn_count = len(reg.list_operations(provider="react-native"))
    assert gws_count >= 15, f"Expected ≥15 gws ops, got {gws_count}"
    assert gh_count >= 15, f"Expected ≥15 gh ops, got {gh_count}"
    assert npm_count >= 10, f"Expected ≥10 npm ops, got {npm_count}"
    assert rn_count >= 10, f"Expected ≥10 react-native ops, got {rn_count}"


def test_registry_total_count():
    reg = Registry()
    reg.load()
    total = len(reg.operations)
    assert total >= 145, f"Expected ≥145 total ops, got {total}"
