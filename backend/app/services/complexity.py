from __future__ import annotations

import json
import re

COMPLEXITY_HEADER = "X-SO-Complexity-Score"
DEFAULT_COMPLEXITY_SCORE = 10


def _clamp(score: int, low: int = 1, high: int = 100) -> int:
    return max(low, min(high, score))


def _estimated_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def score_search_query(query: str) -> int:
    query = (query or "").strip()
    if not query:
        return 1

    score = 5
    score += min(len(query) // 20, 20)

    token_count = len(re.findall(r"\w+", query))
    score += min(token_count * 2, 20)

    operator_count = len(
        re.findall(r"\*|%|\bOR\b|\bAND\b|\bUNION\b|\bSELECT\b|\bDROP\b|\bSLEEP\b|--|;|\"|'", query, flags=re.IGNORECASE)
    )
    score += min(operator_count * 4, 32)

    punctuation_count = len(re.findall(r"[^\w\s]", query))
    density = punctuation_count / max(1, len(query))
    if density >= 0.3:
        score += 12
    elif density >= 0.18:
        score += 7

    return _clamp(score)


def score_ai_payload(payload: dict) -> int:
    messages = payload.get("messages") if isinstance(payload, dict) else None
    prompt = payload.get("prompt", "") if isinstance(payload, dict) else ""

    text_parts: list[str] = []
    message_count = 0

    if isinstance(messages, list):
        message_count = len(messages)
        for message in messages:
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    text_parts.append(content)

    if isinstance(prompt, str) and prompt:
        text_parts.append(prompt)
        message_count = max(message_count, 1)

    joined = "\n".join(text_parts)
    if not joined:
        return DEFAULT_COMPLEXITY_SCORE

    payload_size = len(json.dumps(payload, default=str))
    est_tokens = _estimated_tokens(joined)
    longest_segment = max((len(part) for part in text_parts), default=0)

    score = 8
    score += min(message_count * 3, 18)
    score += min(est_tokens // 20, 32)
    score += min(longest_segment // 120, 20)
    score += min(payload_size // 280, 20)

    marker_count = len(
        re.findall(r"\b(ignore|override|bypass|system prompt|credit card|ssn|password)\b", joined, flags=re.IGNORECASE)
    )
    score += min(marker_count * 3, 12)

    return _clamp(score)


def _graphql_depth(query: str) -> int:
    depth = 0
    max_depth = 0
    for char in query:
        if char == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == "}":
            depth = max(0, depth - 1)
    return max_depth


def score_graphql(payload: dict) -> int:
    if not isinstance(payload, dict):
        return DEFAULT_COMPLEXITY_SCORE

    query = str(payload.get("query", ""))
    variables = payload.get("variables", {})
    if not query.strip():
        return DEFAULT_COMPLEXITY_SCORE

    depth = _graphql_depth(query)
    alias_count = len(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*:\s*[a-zA-Z_]", query))
    argument_count = query.count("(")
    field_tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", query)
    keyword_count = len(re.findall(r"\b(query|mutation|subscription|fragment|on)\b", query))
    field_count = max(0, len(field_tokens) - keyword_count)

    try:
        variables_size = len(json.dumps(variables, default=str))
    except Exception:
        variables_size = 0

    score = 8
    score += min(len(query) // 80, 18)
    score += min(depth * 6, 30)
    score += min(field_count // 8, 20)
    score += min(alias_count * 4, 16)
    score += min(argument_count * 2, 10)
    score += min(variables_size // 180, 18)

    return _clamp(score)
