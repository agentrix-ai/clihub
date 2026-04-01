"""Tests for _parse_extra_args and argument handling."""

from cli_gateway.cli import _parse_extra_args


def test_simple_key_value():
    result = _parse_extra_args(["--name", "Alice", "--age", "30"])
    assert result == {"name": "Alice", "age": 30}


def test_boolean_flag():
    result = _parse_extra_args(["--verbose", "--name", "test"])
    assert result["verbose"] is True
    assert result["name"] == "test"


def test_json_value_parsed():
    result = _parse_extra_args(["--data", '{"key": "value"}'])
    assert result["data"] == {"key": "value"}


def test_list_value_parsed():
    result = _parse_extra_args(["--ids", '[1, 2, 3]'])
    assert result["ids"] == [1, 2, 3]


def test_empty_args():
    result = _parse_extra_args([])
    assert result == {}


def test_trailing_boolean():
    result = _parse_extra_args(["--force"])
    assert result == {"force": True}


def test_bare_json_string():
    result = _parse_extra_args(['{"chat_type": 1, "text": "hello"}'])
    assert result == {"chat_type": 1, "text": "hello"}


def test_numeric_string_stays_string():
    result = _parse_extra_args(["--phone", "13800138000"])
    assert result["phone"] == 13800138000


def test_hyphenated_key():
    result = _parse_extra_args(["--chat-id", "oc_xxx"])
    assert result["chat-id"] == "oc_xxx"
