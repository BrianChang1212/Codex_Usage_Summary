from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "source"))

from token_usage import parse_rollout
from usage_summary import _recommendation, build_usage_summary


class UsageSummaryTest(unittest.TestCase):
    def test_builds_latest_turn_and_session_summary(self):
        events = [
            self.event("turn_context", {"turn_id": "turn-1", "model": "gpt-test"}),
            self.event(
                "response_item",
                {"type": "custom_tool_call", "call_id": "call-1", "name": "ignored"},
            ),
            self.usage("turn-1", "response-1", 1000, 200, 100),
            self.context(1000, 100, 4000, cached=200),
            self.event("turn_context", {"turn_id": "turn-2", "model": "gpt-test"}),
            self.event("response_item", {"type": "function_call", "call_id": "call-2"}),
            self.event("response_item", {"type": "function_call", "call_id": "call-2"}),
            self.event("response_item", {"type": "web_search_call", "call_id": "call-3"}),
            self.usage("turn-2", "response-2a", 1000, 200, 300),
            self.context(1000, 300, 4000, cached=200),
            self.usage("turn-2", "response-2", 3000, 1500, 500),
            self.context(3000, 500, 4000, cached=1500),
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rollout-test.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in events), encoding="utf-8"
            )
            report = parse_rollout(path)

        summary = build_usage_summary(report)

        self.assertEqual(summary["turn_number"], 2)
        self.assertEqual(summary["task_total_tokens"], 4800)
        self.assertEqual(summary["task_input_tokens"], 4000)
        self.assertEqual(summary["task_output_tokens"], 800)
        self.assertEqual(summary["conversation_total_tokens"], 5900)
        self.assertEqual(summary["cache_ratio"], 0.425)
        self.assertEqual(summary["context"], {"tokens": 3000, "window": 4000, "ratio": 0.75})
        self.assertEqual(summary["task_tool_calls"], 2)
        self.assertEqual(summary["conversation_tool_calls"], 3)
        self.assertEqual(summary["cost_label"], "N/A")
        self.assertEqual(summary["next_action"], "Summarize (context is growing)")

    def test_returns_no_summary_when_session_has_no_usage(self):
        self.assertIsNone(build_usage_summary({"records": [], "turns": []}))

    def test_recommends_fresh_context_when_latest_request_is_85_percent(self):
        action = _recommendation(
            task_tools=0,
            subagents=0,
            task_tokens=1000,
            context_window=10000,
            latest_context_ratio=0.85,
            max_context_ratio=0.85,
            compactions=0,
            turn_count=1,
            conversation_tools=0,
        )
        self.assertEqual(action, "Start fresh")

    def test_recommends_splitting_at_75_tool_calls(self):
        action = _recommendation(
            task_tools=75,
            subagents=0,
            task_tokens=1000,
            context_window=10000,
            latest_context_ratio=0.1,
            max_context_ratio=0.1,
            compactions=0,
            turn_count=1,
            conversation_tools=75,
        )
        self.assertEqual(action, "Split task")

    @staticmethod
    def event(event_type: str, payload: dict) -> dict:
        return {"type": event_type, "timestamp": "2026-10-03T12:00:00Z", "payload": payload}

    @classmethod
    def usage(
        cls,
        turn_id: str,
        response_id: str,
        input_tokens: int,
        cached: int,
        output: int,
    ) -> dict:
        return cls.event(
            "token_usage_record",
            {
                "turn_id": turn_id,
                "response_id": response_id,
                "usage": {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": cached,
                    "output_tokens": output,
                    "total_tokens": input_tokens + output,
                },
            },
        )

    @classmethod
    def context(
        cls, input_tokens: int, output_tokens: int, window: int, *, cached: int = 0
    ) -> dict:
        return cls.event(
            "event_msg",
            {
                "type": "token_count",
                "info": {
                    "last_token_usage": {
                        "input_tokens": input_tokens,
                        "cached_input_tokens": cached,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                    },
                    "model_context_window": window,
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
