"""Tests for the search engine."""

from cli_gateway.core.search import search_operations
from cli_gateway.models.operation import Operation


def _make_op(op_id: str, desc: str, desc_en: str = "", keywords: list | None = None) -> Operation:
    parts = op_id.split(".")
    return Operation(
        id=op_id,
        provider=parts[0],
        category=parts[1] if len(parts) > 1 else "",
        name=parts[2] if len(parts) > 2 else "",
        description=desc,
        description_en=desc_en,
        keywords=keywords or [],
    )


SAMPLE_OPS = [
    _make_op("lark.im.messages_send", "发送消息到群聊或单聊", "Send a message", ["消息", "发送", "聊天", "im"]),
    _make_op("wecom.msg.send_message", "向单聊或群聊发送文本消息", "Send text message", ["消息", "发送", "msg"]),
    _make_op("dingtalk.todo.task_create", "创建待办任务", "Create a todo task", ["待办", "任务", "todo"]),
    _make_op("lark.calendar.agenda", "查看日历日程列表", "View calendar agenda", ["日历", "日程", "calendar"]),
    _make_op("wecom.meeting.create_meeting", "创建预约会议", "Create a meeting", ["会议", "meeting"]),
    _make_op("dingtalk.attendance.record_get", "查看考勤打卡记录", "Get attendance records", ["考勤", "打卡"]),
    _make_op("lark.docs.create", "创建飞书文档", "Create a document", ["文档", "docs"]),
    _make_op("lark.task.create", "创建任务", "Create a task", ["任务", "待办", "task"]),
]


def test_search_chinese_message():
    results = search_operations("发消息", SAMPLE_OPS)
    assert len(results) > 0
    ids = [op.id for op, _ in results]
    assert "lark.im.messages_send" in ids or "wecom.msg.send_message" in ids


def test_search_english_todo():
    results = search_operations("todo", SAMPLE_OPS)
    assert len(results) > 0
    ids = [op.id for op, _ in results]
    assert "dingtalk.todo.task_create" in ids


def test_search_filter_provider():
    results = search_operations("消息", SAMPLE_OPS, provider="wecom")
    assert all(op.provider == "wecom" for op, _ in results)


def test_search_filter_category():
    results = search_operations("日程", SAMPLE_OPS, category="calendar")
    assert all(op.category == "calendar" for op, _ in results)


def test_search_top_k():
    results = search_operations("任务", SAMPLE_OPS, top_k=2)
    assert len(results) <= 2


def test_search_no_match():
    results = search_operations("zzzzz_nonexistent", SAMPLE_OPS)
    assert len(results) == 0


def test_search_empty_operations():
    results = search_operations("任务", [])
    assert results == []


def test_search_calendar():
    results = search_operations("查看日程", SAMPLE_OPS)
    assert len(results) > 0
    top_id = results[0][0].id
    assert "calendar" in top_id or "schedule" in top_id


def test_search_meeting():
    results = search_operations("会议", SAMPLE_OPS)
    assert len(results) > 0
    ids = [op.id for op, _ in results]
    assert "wecom.meeting.create_meeting" in ids
