"""Codex Stop hook for compact local usage telemetry."""

from __future__ import annotations

import json
import os
import argparse
import time
from pathlib import Path
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN_ROOT / "source"))

from token_usage import parse_rollout
from usage_summary import build_usage_summary


def format_count(value: int) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}".rstrip("0").rstrip(".") + "B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}".rstrip("0").rstrip(".") + "K"
    return str(value)


def format_percent(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "N/A"


def format_hook_message(summary: dict) -> str:
    count = format_count
    total = (
        f"Total: {count(summary['task_total_tokens'])} tokens "
        f"(input {count(summary['task_input_tokens'])} / "
        f"output {count(summary['task_output_tokens'])})"
    )
    total += f" | Conversation: {count(summary['conversation_total_tokens'])}"
    context = summary.get("context")
    context_percent = format_percent(context["ratio"] if context else None)
    context_counts = (
        f"{count(context['tokens'])} / {count(context['window'])}"
        if context
        else "N/A"
    )
    cache = format_percent(summary.get("cache_ratio"))
    tools = (
        f"Tools: task {summary['task_tool_calls']} / "
        f"conversation {summary['conversation_tool_calls']}"
    )
    action = summary["next_action"]
    labels = {
        "Continue": "Continue",
        "Summarize (context is growing)": "Summarize (context is growing)",
        "Start fresh": "Start fresh",
        "Split task": "Split task",
    }
    action = labels.get(action, action)
    return "\n".join(
        (
            total,
            f"Cache: {cache} | Context: {context_percent} ({context_counts}) | {tools}",
            f"Cost: N/A | Next: {action}",
        )
    )


def find_rollout(codex_home: Path, thread_id: str) -> Path | None:
    if not thread_id or any(char in thread_id for char in "/\\*?[]"):
        return None
    pattern = f"*{thread_id}*.jsonl"
    for folder in ("sessions", "archived_sessions"):
        root = codex_home / folder
        if not root.is_dir():
            continue
        try:
            match = next(root.rglob(pattern), None)
        except OSError:
            continue
        if match is not None and match.is_file():
            return match
    return None


def build_message(codex_home: Path, thread_id: str) -> str:
    rollout = find_rollout(codex_home, thread_id)
    if rollout is None:
        return ""
    summary = build_usage_summary(parse_rollout(rollout))
    if summary is None:
        return ""
    return format_hook_message(summary)


def run_hook(codex_home: Path, thread_id: str) -> str:
    message = build_message(codex_home, thread_id)
    if not message:
        return ""
    return json.dumps(
        {"systemMessage": message}, ensure_ascii=False, separators=(",", ":")
    )


def run_hook_event(codex_home: Path, hook_input: dict) -> str:
    transcript = hook_input.get("transcript_path")
    session_id = hook_input.get("session_id", "")
    if isinstance(transcript, str) and transcript:
        candidate = Path(transcript).expanduser()
        try:
            resolved = candidate.resolve(strict=True)
            allowed_roots = (
                (codex_home / "sessions").resolve(),
                (codex_home / "archived_sessions").resolve(),
            )
            is_allowed = any(resolved.is_relative_to(root) for root in allowed_roots)
            matches_session = not session_id or session_id in resolved.name
            if is_allowed and matches_session and resolved.suffix == ".jsonl":
                summary = build_usage_summary(parse_rollout(resolved))
                if summary is not None:
                    message = format_hook_message(summary)
                    return json.dumps(
                        {"systemMessage": message},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
        except (OSError, RuntimeError, ValueError):
            pass
    return run_hook(codex_home, str(session_id))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hook", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--format", choices=("compact",), default="compact", help="輸出精簡摘要"
    )
    args = parser.parse_args()
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    if args.hook:
        try:
            hook_input = json.load(sys.stdin)
            if not isinstance(hook_input, dict):
                hook_input = {}
            time.sleep(0.12)
            output = run_hook_event(home, hook_input)
        except Exception:
            output = "{}"
    else:
        output = build_message(home, os.environ.get("CODEX_THREAD_ID", ""))
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
