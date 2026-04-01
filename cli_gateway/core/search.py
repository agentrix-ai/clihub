"""Search engine — keyword + Chinese tokenization (jieba) + BM25-lite ranking."""

from __future__ import annotations

import math
import re
from collections import Counter

from cli_gateway.models.operation import Operation

_jieba_loaded = False


def _ensure_jieba():
    global _jieba_loaded
    if not _jieba_loaded:
        import jieba
        jieba.setLogLevel(20)  # suppress jieba debug output
        _jieba_loaded = True


SYNONYMS: dict[str, list[str]] = {
    "发消息": ["send_message", "im", "msg", "消息", "message", "发送"],
    "待办": ["todo", "task", "任务", "待办事项"],
    "会议": ["meeting", "会议室", "conference", "视频会议", "calendar"],
    "日程": ["schedule", "calendar", "日历", "agenda", "event"],
    "通讯录": ["contact", "联系人", "成员", "user", "通讯录"],
    "文档": ["doc", "document", "文件", "文档", "docs"],
    "表格": ["sheet", "table", "smartsheet", "aitable", "base", "表格", "智能表格", "多维表格"],
    "邮件": ["mail", "email", "邮箱"],
    "审批": ["approval", "oa", "审批"],
    "考勤": ["attendance", "打卡", "排班"],
    "群聊": ["chat", "group", "群", "群消息"],
    "云盘": ["drive", "文件", "上传", "下载"],
}


def _expand_query(query: str) -> list[str]:
    """Expand query with synonyms."""
    tokens = _tokenize(query)
    expanded = list(tokens)
    query_lower = query.lower()
    for key, syns in SYNONYMS.items():
        if key in query_lower or any(s in query_lower for s in syns):
            expanded.extend(syns)
    return expanded


def _tokenize(text: str) -> list[str]:
    """Tokenize text with jieba for Chinese, split on whitespace/punctuation for others."""
    _ensure_jieba()
    import jieba
    words = jieba.lcut(text.lower())
    ascii_words = re.findall(r"[a-z_][a-z0-9_]*", text.lower())
    return [w for w in set(words + ascii_words) if len(w) > 1]


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avg_dl: float,
    df: dict[str, int],
    n_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Simplified BM25 scoring."""
    tf = Counter(doc_tokens)
    dl = len(doc_tokens)
    score = 0.0
    for q in query_tokens:
        if q not in tf:
            continue
        freq = tf[q]
        doc_freq = df.get(q, 0)
        idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
        tf_norm = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / max(avg_dl, 1)))
        score += idf * tf_norm
    return score


def search_operations(
    query: str,
    operations: list[Operation],
    provider: str | None = None,
    category: str | None = None,
    top_k: int = 10,
) -> list[tuple[Operation, float]]:
    """Search operations by query string, return (operation, score) pairs sorted by relevance."""
    if not operations:
        return []

    candidates = operations
    if provider:
        candidates = [o for o in candidates if o.provider == provider]
    if category:
        candidates = [o for o in candidates if o.category == category]

    if not candidates:
        return []

    query_tokens = _expand_query(query)
    if not query_tokens:
        return [(op, 0.0) for op in candidates[:top_k]]

    doc_token_cache: list[list[str]] = []
    df: dict[str, int] = Counter()

    for op in candidates:
        tokens = _tokenize(op.search_text)
        doc_token_cache.append(tokens)
        for t in set(tokens):
            df[t] += 1

    n_docs = len(candidates)
    avg_dl = sum(len(t) for t in doc_token_cache) / max(n_docs, 1)

    scored: list[tuple[Operation, float]] = []
    for op, doc_tokens in zip(candidates, doc_token_cache):
        score = _bm25_score(query_tokens, doc_tokens, avg_dl, df, n_docs)
        if score > 0:
            scored.append((op, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
