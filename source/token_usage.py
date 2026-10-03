"""Read usage metadata and count tool calls without exposing transcript text."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import json


USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _usage(raw: Any) -> dict[str, int] | None:
    if not isinstance(raw, dict):
        return None
    if not any(field in raw for field in USAGE_FIELDS):
        return None
    result = {field: _nonnegative_int(raw.get(field)) for field in USAGE_FIELDS}
    if not result["total_tokens"]:
        result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
    return result


def _signature(turn_id: str, usage: dict[str, int]) -> tuple[Any, ...]:
    return (turn_id, *(usage[field] for field in USAGE_FIELDS))


def _row_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return _signature(row["turn_id"], row["usage"])


def _short_id(value: str) -> str:
    return value[-8:] if len(value) > 8 else value


def parse_rollout(path: Path) -> dict[str, Any]:
    """Parse usage records and aggregate call metadata, never transcript text."""
    modern_rows: list[dict[str, Any]] = []
    legacy_rows: list[dict[str, Any]] = []
    models_by_turn: dict[str, str] = {}
    context_by_turn: dict[str, int] = {}
    tool_calls_by_turn: dict[str, set[str]] = defaultdict(set)
    subagents_by_turn: dict[str, set[str]] = defaultdict(set)
    compactions_by_turn: Counter[str] = Counter()
    seen_responses: set[str] = set()
    malformed_lines = 0
    skipped_records = 0
    current_turn_id = ""
    current_model = ""

    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError as exc:
        return {
            "error": f"無法讀取所選 session（{type(exc).__name__}）",
            "records": [],
            "turns": [],
            "totals": _empty_totals(),
            "warnings": [],
        }

    with handle:
        for ordinal, line in enumerate(handle, start=1):
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                malformed_lines += 1
                continue
            if not isinstance(event, dict):
                continue

            timestamp = event.get("timestamp")
            timestamp = timestamp if isinstance(timestamp, str) else ""
            event_type = event.get("type")
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue

            if event_type == "response_item":
                payload_type = payload.get("type")
                if isinstance(payload_type, str) and payload_type.endswith("_call"):
                    call_turn = payload.get("turn_id") or current_turn_id
                    call_id = payload.get("call_id") or payload.get("id")
                    if not isinstance(call_id, str) or not call_id:
                        call_id = f"line-{ordinal}"
                    if isinstance(call_turn, str) and call_turn:
                        tool_calls_by_turn[call_turn].add(call_id)
                continue

            if event_type == "event_msg":
                payload_kind = payload.get("type")
                if payload_kind == "context_compacted":
                    compacted_turn = payload.get("turn_id") or current_turn_id
                    if isinstance(compacted_turn, str) and compacted_turn:
                        compactions_by_turn[compacted_turn] += 1
                    continue
                if payload_kind == "sub_agent_activity" and payload.get("kind") == "started":
                    child_id = payload.get("agent_thread_id")
                    child_turn = payload.get("turn_id") or current_turn_id
                    if (
                        isinstance(child_id, str)
                        and child_id
                        and isinstance(child_turn, str)
                        and child_turn
                    ):
                        subagents_by_turn[child_turn].add(child_id)
                    continue

            if event_type == "turn_context":
                turn_id = payload.get("turn_id")
                if isinstance(turn_id, str):
                    current_turn_id = turn_id
                    model = payload.get("model")
                    if isinstance(model, str) and model:
                        current_model = model
                        models_by_turn[turn_id] = model
                continue

            if event_type == "token_usage_record":
                raw_usage = _usage(payload.get("usage"))
                response_id = payload.get("response_id")
                turn_id = payload.get("turn_id")
                turn_id = turn_id if isinstance(turn_id, str) else current_turn_id
                if raw_usage is None:
                    skipped_records += 1
                    continue
                if isinstance(response_id, str) and response_id:
                    if response_id in seen_responses:
                        skipped_records += 1
                        continue
                    seen_responses.add(response_id)
                modern_rows.append(
                    {
                        "timestamp": timestamp,
                        "ordinal": ordinal,
                        "turn_id": turn_id,
                        "response_id": response_id if isinstance(response_id, str) else "",
                        "model": models_by_turn.get(turn_id, current_model),
                        "source": "token_usage_record",
                        "usage": raw_usage,
                    }
                )
                continue

            if event_type == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info")
                if not isinstance(info, dict):
                    continue
                raw_usage = _usage(info.get("last_token_usage"))
                context_window = _nonnegative_int(info.get("model_context_window"))
                if context_window:
                    if current_turn_id:
                        context_by_turn[current_turn_id] = context_window
                if raw_usage is None:
                    skipped_records += 1
                    continue
                legacy_rows.append(
                    {
                        "timestamp": timestamp,
                        "ordinal": ordinal,
                        "turn_id": current_turn_id,
                        "response_id": "",
                        "model": models_by_turn.get(current_turn_id, current_model),
                        "source": "token_count.last_token_usage",
                        "usage": raw_usage,
                        "context_window": context_window,
                    }
                )

    # New and legacy events can describe the same response. Match their usage
    # tuples as a multiset so repeated responses with identical counts survive.
    modern_counts = Counter(_row_signature(row) for row in modern_rows)
    generic_counts = Counter(tuple(row["usage"][field] for field in USAGE_FIELDS) for row in modern_rows)
    records = list(modern_rows)
    for row in legacy_rows:
        exact = _row_signature(row)
        generic = tuple(row["usage"][field] for field in USAGE_FIELDS)
        if modern_counts[exact] > 0:
            modern_counts[exact] -= 1
            generic_counts[generic] -= 1
            continue
        if not row["turn_id"] and generic_counts[generic] > 0:
            generic_counts[generic] -= 1
            continue
        records.append(row)

    for row in records:
        window = row.get("context_window") or context_by_turn.get(row["turn_id"], 0)
        row["context_window"] = window
        row["context_percent"] = (
            round(row["usage"]["input_tokens"] * 100 / window, 1) if window else None
        )
        row["turn_id_short"] = _short_id(row["turn_id"])
        row["response_id_short"] = _short_id(row["response_id"])

    records.sort(key=lambda row: (row["timestamp"], row["ordinal"]))
    turn_ids: dict[str, int] = {}
    turns_by_id: dict[str, dict[str, Any]] = {}
    totals = _empty_totals()
    for index, row in enumerate(records, start=1):
        turn_id = row["turn_id"] or "unknown"
        if turn_id not in turns_by_id:
            turn_ids[turn_id] = len(turn_ids) + 1
            turns_by_id[turn_id] = {
                "turn_number": turn_ids[turn_id],
                "turn_id": "" if turn_id == "unknown" else turn_id,
                "first_timestamp": row["timestamp"],
                "last_timestamp": row["timestamp"],
                "responses": 0,
                "models": [],
                "totals": _empty_totals(),
            }
        turn = turns_by_id[turn_id]
        turn["responses"] += 1
        turn["last_timestamp"] = row["timestamp"]
        if row["model"] and row["model"] not in turn["models"]:
            turn["models"].append(row["model"])
        row["response_number"] = index
        row["turn_number"] = turn["turn_number"]
        for field in USAGE_FIELDS:
            value = row["usage"][field]
            turn["totals"][field] += value
            totals[field] += value

    for row in records:
        row.pop("turn_id", None)
        row.pop("response_id", None)

    turns = []
    for turn in turns_by_id.values():
        turn_copy = {key: value for key, value in turn.items() if key != "turn_id"}
        turn_copy["turn_id_short"] = _short_id(turn.get("turn_id", ""))
        turn_id = turn.get("turn_id", "")
        turn_copy["tool_calls"] = len(tool_calls_by_turn.get(turn_id, set()))
        turn_copy["subagents"] = len(subagents_by_turn.get(turn_id, set()))
        turn_copy["compactions"] = compactions_by_turn.get(turn_id, 0)
        turns.append(turn_copy)

    warnings = []
    if malformed_lines:
        warnings.append(f"略過 {malformed_lines} 行無法解析的 JSONL（通常是檔案尾端尚未寫完）")
    if skipped_records:
        warnings.append(f"略過 {skipped_records} 筆缺少有效 token 欄位的紀錄")
    if not records:
        warnings.append("此 session 尚無可辨識的 token usage 紀錄")

    return {
        "error": "",
        "records": records,
        "turns": turns,
        "totals": totals,
        "tool_call_count": sum(len(calls) for calls in tool_calls_by_turn.values()),
        "warnings": warnings,
        "record_count": len(records),
        "format_counts": {
            "token_usage_record": len(modern_rows),
            "token_count_fallback": len(records) - len(modern_rows),
        },
    }


def _empty_totals() -> dict[str, int]:
    return {field: 0 for field in USAGE_FIELDS}
