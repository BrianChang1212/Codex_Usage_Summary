"""Build a compact latest-turn summary from locally recorded rollout data."""

from __future__ import annotations

from typing import Any


def build_usage_summary(report: dict[str, Any]) -> dict[str, Any] | None:
    """Summarize the latest recorded turn and its containing session."""
    turns = report.get("turns") or []
    records = report.get("records") or []
    if not turns:
        return None

    latest_turn = turns[-1]
    turn_number = latest_turn["turn_number"]
    turn_records = [
        row for row in records if row.get("turn_number") == turn_number
    ]
    context_records = [
        row
        for row in turn_records
        if row.get("context_window") and row.get("context_percent") is not None
    ]
    latest_context = context_records[-1] if context_records else None
    max_context = (
        max(context_records, key=lambda row: row["context_percent"])
        if context_records
        else None
    )

    totals = latest_turn["totals"]
    input_tokens = totals["input_tokens"]
    cached_tokens = totals["cached_input_tokens"]
    context = (
        {
            "tokens": max_context["usage"]["input_tokens"],
            "window": max_context["context_window"],
            "ratio": max_context["context_percent"] / 100,
        }
        if max_context
        else None
    )
    latest_ratio = (
        latest_context["context_percent"] / 100 if latest_context else 0.0
    )
    task_tools = latest_turn.get("tool_calls", 0)
    conversation_tools = report.get(
        "tool_call_count",
        sum(turn.get("tool_calls", 0) for turn in turns),
    )
    action = _recommendation(
        task_tools=task_tools,
        subagents=latest_turn.get("subagents", 0),
        task_tokens=totals["total_tokens"],
        context_window=context["window"] if context else 0,
        latest_context_ratio=latest_ratio,
        max_context_ratio=context["ratio"] if context else 0.0,
        compactions=latest_turn.get("compactions", 0),
        turn_count=len(turns),
        conversation_tools=conversation_tools,
    )

    return {
        "turn_number": turn_number,
        "timestamp": latest_turn["last_timestamp"],
        "models": latest_turn["models"],
        "task_total_tokens": totals["total_tokens"],
        "task_input_tokens": input_tokens,
        "task_output_tokens": totals["output_tokens"],
        "conversation_total_tokens": report["totals"]["total_tokens"],
        "cache_ratio": cached_tokens / input_tokens if input_tokens else 0.0,
        "context": context,
        "task_tool_calls": task_tools,
        "conversation_tool_calls": conversation_tools,
        "cost_label": "N/A",
        "next_action": action,
    }


def _recommendation(
    *,
    task_tools: int,
    subagents: int,
    task_tokens: int,
    context_window: int,
    latest_context_ratio: float,
    max_context_ratio: float,
    compactions: int,
    turn_count: int,
    conversation_tools: int,
) -> str:
    if (
        task_tools >= 75
        or (task_tools >= 40 and subagents >= 4)
        or (context_window and task_tokens >= 3 * context_window and task_tools >= 40)
    ):
        return "Split task"
    if latest_context_ratio >= 0.85:
        return "Start fresh"
    if (
        latest_context_ratio >= 0.65
        or (max_context_ratio >= 0.80 and compactions == 0)
        or turn_count >= 12
        or conversation_tools >= 120
    ):
        return "Summarize (context is growing)"
    return "Continue"
