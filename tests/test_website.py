"""Tests for clihub-web API endpoints."""

import sys
from pathlib import Path

import pytest

# Add website dir to path so we can import app
WEBSITE_DIR = Path(__file__).resolve().parent.parent / "website"
sys.path.insert(0, str(WEBSITE_DIR))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["schemas"] >= 4
    assert data["total_operations"] >= 80


def test_api_providers(client):
    r = client.get("/api/providers")
    assert r.status_code == 200
    providers = r.json()
    assert isinstance(providers, list)
    assert len(providers) >= 4
    names = {p["name"] for p in providers}
    assert {"wecom", "dingtalk", "lark", "dreamina"} <= names
    for p in providers:
        assert "tools_count" in p
        assert p["tools_count"] > 0
        assert "display_name" in p


def test_api_schemas_all(client):
    r = client.get("/api/schemas")
    assert r.status_code == 200
    schemas = r.json()
    assert isinstance(schemas, dict)
    assert len(schemas) >= 4
    for name, data in schemas.items():
        assert "operations" in data
        assert len(data["operations"]) > 0


def test_api_schema_single(client):
    r = client.get("/api/schemas/wecom")
    assert r.status_code == 200
    data = r.json()
    assert data.get("provider") == "wecom"
    assert len(data["operations"]) > 0


def test_api_schema_not_found(client):
    r = client.get("/api/schemas/nonexistent")
    assert r.status_code == 404


def test_api_version(client):
    r = client.get("/api/version")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert "updated_at" in data
    assert data["schema_count"] >= 4


def test_landing_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "cli-hub" in r.text
    assert "pip install agent-cli-hub" in r.text
    assert "WeCom" in r.text
    assert "DingTalk" in r.text
    assert "Dreamina" in r.text


def test_static_css(client):
    r = client.get("/static/style.css")
    assert r.status_code == 200
    assert "font-family" in r.text
