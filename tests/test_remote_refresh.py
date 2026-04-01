"""Tests for remote schema refresh and local cache priority."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cli_gateway.core.registry import Registry, _LOCAL_CACHE_DIR, REMOTE_REGISTRY_URL


def test_remote_registry_url_configured():
    assert REMOTE_REGISTRY_URL == "https://clihub.cc/api/schemas"


def test_local_cache_dir_path():
    assert _LOCAL_CACHE_DIR == Path.home() / ".cli-hub" / "schemas"


def test_load_prefers_local_cache_over_builtin():
    """If a schema exists in local cache, it should be loaded instead of built-in."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        custom_schema = {
            "provider": "wecom",
            "version": "99.0.0",
            "operations": [
                {
                    "category": "test",
                    "name": "cached_op",
                    "description": "From local cache",
                    "keywords": ["test"],
                    "argv_template": ["wecom-cli", "test"],
                }
            ],
        }
        (cache_dir / "wecom.json").write_text(
            json.dumps(custom_schema), encoding="utf-8"
        )

        with patch("cli_gateway.core.registry._LOCAL_CACHE_DIR", cache_dir):
            reg = Registry()
            reg.load()

            wecom_ops = [o for o in reg.operations if o.provider == "wecom"]
            assert any(o.name == "cached_op" for o in wecom_ops)
            assert not any(o.name == "get_userlist" for o in wecom_ops)


def test_load_falls_back_to_builtin_when_no_cache():
    """If local cache is empty, built-in schemas should load normally."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_cache = Path(tmpdir) / "nonexistent"
        with patch("cli_gateway.core.registry._LOCAL_CACHE_DIR", empty_cache):
            reg = Registry()
            reg.load()
            assert len(reg.operations) > 0
            wecom_ops = [o for o in reg.operations if o.provider == "wecom"]
            assert len(wecom_ops) > 0


def test_load_discovers_new_providers_from_cache():
    """If cache contains a provider not in BUILTIN_PROVIDERS, it should still load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        new_provider_schema = {
            "provider": "newcli",
            "version": "1.0.0",
            "operations": [
                {
                    "category": "demo",
                    "name": "hello",
                    "description": "New provider from remote",
                    "keywords": ["new"],
                    "argv_template": ["newcli", "hello"],
                }
            ],
        }
        (cache_dir / "newcli.json").write_text(
            json.dumps(new_provider_schema), encoding="utf-8"
        )

        with patch("cli_gateway.core.registry._LOCAL_CACHE_DIR", cache_dir):
            reg = Registry()
            reg.load()
            new_ops = [o for o in reg.operations if o.provider == "newcli"]
            assert len(new_ops) == 1
            assert new_ops[0].name == "hello"


def test_pull_remote_schemas_saves_to_cache(tmp_path):
    """_pull_remote_schemas should save JSON files to cache dir."""
    import httpx as httpx_mod
    from cli_gateway.cli import _pull_remote_schemas

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "wecom": {"provider": "wecom", "operations": [{"name": "test"}]},
        "lark": {"provider": "lark", "operations": [{"name": "test2"}]},
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    cache_dir = tmp_path / "cache"

    with patch("httpx.Client") as mock_cls:
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        _pull_remote_schemas("https://clihub.cc/api/schemas", cache_dir)

    assert (cache_dir / "wecom.json").exists()
    assert (cache_dir / "lark.json").exists()
    data = json.loads((cache_dir / "wecom.json").read_text())
    assert data["provider"] == "wecom"


def test_pull_remote_schemas_graceful_failure(tmp_path):
    """Network failure should not crash, just print warning."""
    import httpx as httpx_mod
    from cli_gateway.cli import _pull_remote_schemas

    cache_dir = tmp_path / "cache"

    with patch("httpx.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx_mod.ConnectError("connection refused")
        _pull_remote_schemas("https://clihub.cc/api/schemas", cache_dir)

    assert not cache_dir.exists() or len(list(cache_dir.glob("*.json"))) == 0
