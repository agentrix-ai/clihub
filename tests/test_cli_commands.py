"""End-to-end tests for all CLI commands via typer CliRunner."""

import json

from typer.testing import CliRunner

from cli_gateway.cli import app

runner = CliRunner()


# ── version ──────────────────────────────────────────────

def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "cli-hub v" in result.output


# ── search ───────────────────────────────────────────────

def test_search_chinese():
    result = runner.invoke(app, ["search", "发消息"])
    assert result.exit_code == 0
    assert "send_message" in result.output or "messages_send" in result.output


def test_search_english():
    result = runner.invoke(app, ["search", "calendar"])
    assert result.exit_code == 0
    assert "calendar" in result.output


def test_search_json_output():
    result = runner.invoke(app, ["search", "发消息", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "score" in data[0]
    assert "input_schema" in data[0]


def test_search_filter_provider():
    result = runner.invoke(app, ["search", "消息", "--provider", "wecom"])
    assert result.exit_code == 0
    assert "wecom" in result.output


def test_search_top_k():
    result = runner.invoke(app, ["search", "任务", "--top", "2"])
    assert result.exit_code == 0


def test_search_low_relevance_still_returns():
    """BM25 may return low-score results for nonsense queries — verify no crash."""
    result = runner.invoke(app, ["search", "zzzzz_nonexistent_query"])
    assert result.exit_code == 0 or "No matching" in result.output


# ── info ─────────────────────────────────────────────────

def test_info_found():
    result = runner.invoke(app, ["info", "lark.calendar.agenda"])
    assert result.exit_code == 0
    assert "lark.calendar.agenda" in result.output
    assert "calendar" in result.output


def test_info_json_output():
    result = runner.invoke(app, ["info", "lark.calendar.agenda", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "lark.calendar.agenda"
    assert data["provider"] == "lark"


def test_info_not_found():
    result = runner.invoke(app, ["info", "fake.nonexistent.op"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_info_shows_parameters():
    result = runner.invoke(app, ["info", "wecom.todo.get_todo_detail"])
    assert result.exit_code == 0
    assert "todo_id_list" in result.output


def test_info_shows_example():
    result = runner.invoke(app, ["info", "wecom.msg.send_message"])
    assert result.exit_code == 0
    assert "Example" in result.output


# ── list ─────────────────────────────────────────────────

def test_list_providers():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "wecom" in result.output
    assert "dingtalk" in result.output
    assert "lark" in result.output


def test_list_providers_json():
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    names = [p["name"] for p in data]
    assert "wecom" in names
    assert "dingtalk" in names
    assert "lark" in names
    assert all("tools_count" in p for p in data)


def test_list_provider_tools():
    result = runner.invoke(app, ["list", "wecom"])
    assert result.exit_code == 0
    assert "wecom.todo" in result.output or "wecom.msg" in result.output


def test_list_provider_tools_json():
    result = runner.invoke(app, ["list", "wecom", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) > 0
    assert all(d["id"].startswith("wecom.") for d in data)


def test_list_provider_category_filter():
    result = runner.invoke(app, ["list", "wecom", "--category", "todo"])
    assert result.exit_code == 0
    assert "todo" in result.output


def test_list_provider_no_tools():
    result = runner.invoke(app, ["list", "wecom", "--category", "nonexistent_cat"])
    assert result.exit_code == 1
    assert "No tools found" in result.output


def test_list_all_three_providers_have_tools():
    for provider in ["wecom", "dingtalk", "lark"]:
        result = runner.invoke(app, ["list", provider, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) > 0, f"{provider} should have tools loaded"


# ── doctor ───────────────────────────────────────────────

def test_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "CLI Hub Doctor" in result.output
    assert "operations loaded" in result.output


def test_doctor_shows_all_providers():
    result = runner.invoke(app, ["doctor"])
    assert "WeCom" in result.output or "wecom" in result.output.lower()
    assert "DingTalk" in result.output or "dingtalk" in result.output.lower()
    assert "Lark" in result.output or "lark" in result.output.lower()


# ── refresh ──────────────────────────────────────────────

def test_refresh_loads_static():
    result = runner.invoke(app, ["refresh"])
    assert result.exit_code == 0
    assert "operations from static schemas" in result.output
    assert "Total:" in result.output


# ── install ──────────────────────────────────────────────

def test_install_no_args():
    result = runner.invoke(app, ["install"])
    assert result.exit_code == 1
    assert "Specify a provider" in result.output


def test_install_unknown_provider():
    result = runner.invoke(app, ["install", "nonexistent_provider"])
    assert result.exit_code == 1
    assert "Unknown provider" in result.output


# ── auth ─────────────────────────────────────────────────

def test_auth_unknown_provider():
    result = runner.invoke(app, ["auth", "nonexistent_provider"])
    assert result.exit_code == 1
    assert "Unknown provider" in result.output


def test_auth_status():
    result = runner.invoke(app, ["auth", "--status"])
    assert result.exit_code == 0
    assert "Provider Status" in result.output


# ── run ──────────────────────────────────────────────────

def test_run_operation_not_found():
    result = runner.invoke(app, ["run", "fake.nonexistent.op"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output


def test_run_invalid_json_args():
    result = runner.invoke(app, ["run", "wecom.msg.send_message", "--args", "not_json{"])
    assert "Invalid JSON" in result.output or result.exit_code != 0


# ── help ─────────────────────────────────────────────────

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "install" in result.output
    assert "auth" in result.output
    assert "run" in result.output
    assert "info" in result.output
    assert "doctor" in result.output


def test_search_help():
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--provider" in result.output
    assert "--json" in result.output
