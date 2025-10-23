"""Helpers to normalize raw LLM outputs into structured content."""

import json
from typing import Any


def _strip_code_fence(text: str) -> str:
    """Remove leading markdown fences such as ```json ... ``` if present."""
    stripped = text.strip()
    if stripped.startswith("```"):
        parts = stripped.split("\n", 1)
        if len(parts) == 2:
            stripped = parts[1]
        stripped = stripped.rstrip("`").strip()
    return stripped


def _try_parse_json(text: str):
    """Attempt to parse JSON text; return None when parsing fails."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def normalize_response_content(raw_content: Any) -> Any:
    """
    Normalize LLM output into structured JSON where possible.

    - Strings: strip markdown fences, try to `json.loads`, else collapse whitespace.
    - Lists: flatten chunked responses before re-normalizing.
    - Other types: returned unchanged.
    """
    if isinstance(raw_content, str):
        stripped = _strip_code_fence(raw_content)
        parsed = _try_parse_json(stripped)
        if parsed is not None:
            return parsed
        return " ".join(stripped.split())

    if isinstance(raw_content, list):
        collected = []
        for chunk in raw_content:
            if isinstance(chunk, dict):
                collected.append(chunk.get("text", ""))
            else:
                collected.append(str(chunk))
        combined = " ".join(" ".join(collected).split())
        if not combined:
            return ""
        return normalize_response_content(combined)

    return raw_content


def _safe_number(value: Any) -> float:
    """Best-effort conversion of a score value to a numeric type."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _coerce_total(value: float) -> Any:
    """Return int when the value is whole, otherwise keep float."""
    if value.is_integer():
        return int(value)
    return value


def ensure_totals(response: Any) -> Any:
    """
    Recompute cumulative totals for each score key based on the analysis entries.

    The response is returned unchanged when analysis data is missing or malformed.
    """
    if not isinstance(response, dict):
        return response

    analysis = response.get("analysis")
    if not isinstance(analysis, list):
        return response

    totals = {}
    for entry in analysis:
        if not isinstance(entry, dict):
            continue
        score = entry.get("score")
        if not isinstance(score, dict):
            continue
        for key, value in score.items():
            totals[key] = totals.get(key, 0.0) + _safe_number(value)

    if not totals:
        return response

    aggregated = {
        f"{key}_sum": _coerce_total(total)
        for key, total in totals.items()
    }
    response["totals"] = aggregated
    return response
