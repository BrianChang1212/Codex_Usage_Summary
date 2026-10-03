from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PROJECT_ROOT / "source"))
sys.path.insert(0, str(PROJECT_ROOT / "plugin" / "scripts"))

from usage_hook import find_rollout, format_hook_message, run_hook, run_hook_event


class PluginReportTest(unittest.TestCase):
    def test_hook_prints_compact_three_line_system_message_for_current_thread(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            sessions = home / "sessions" / "2026" / "10" / "03"
            sessions.mkdir(parents=True)
            thread_id = "12345678-1234-1234-1234-123456789abc"
            rollout = sessions / f"rollout-2026-10-03T12-00-00-{thread_id}.jsonl"
            events = [
                {"type": "turn_context", "payload": {"turn_id": "turn-1", "model": "gpt-test"}},
                {
                    "type": "token_usage_record",
                    "timestamp": "2026-10-03T12:00:00Z",
                    "payload": {
                        "turn_id": "turn-1",
                        "response_id": "response-1",
                        "usage": {
                            "input_tokens": 1000,
                            "cached_input_tokens": 500,
                            "output_tokens": 200,
                            "total_tokens": 1200,
                        },
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {"input_tokens": 1000, "cached_input_tokens": 500, "output_tokens": 200, "total_tokens": 1200},
                            "model_context_window": 4000,
                        },
                    },
                },
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in events), encoding="utf-8")

            output = run_hook(home, thread_id)

        message = json.loads(output)["systemMessage"]
        self.assertIn("Total: 1.2K tokens (input 1K / output 200) | Conversation: 1.2K", message)
        self.assertIn("Cache: 50.0% | Context: 25.0% (1K / 4K) | Tools: task 0 / conversation 0", message)
        self.assertIn("Cost: N/A | Next: Continue", message)
        self.assertEqual(len(message.splitlines()), 3)

    def test_locates_rollout_from_nested_sessions_and_archived_sessions(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            thread_id = "aabbccdd-1234-1234-1234-123456789abc"
            archived = home / "archived_sessions" / "2026" / "10"
            archived.mkdir(parents=True)
            expected = archived / f"rollout-2026-10-03T12-00-00-{thread_id}.jsonl"
            expected.touch()
            self.assertEqual(find_rollout(home, thread_id), expected)

    def test_hook_silently_skips_when_thread_is_missing_or_has_no_usage(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(run_hook(Path(temp), "missing-thread"), "")

    def test_hook_uses_transcript_path_from_codex_event_without_env_thread_id(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            sessions = home / "sessions" / "2026" / "10" / "03"
            sessions.mkdir(parents=True)
            thread_id = "12345678-1234-1234-1234-123456789abc"
            rollout = sessions / f"rollout-2026-10-03T12-00-00-{thread_id}.jsonl"
            events = [
                {"type": "turn_context", "payload": {"turn_id": "turn-1", "model": "gpt-test"}},
                {
                    "type": "token_usage_record",
                    "payload": {
                        "turn_id": "turn-1",
                        "response_id": "response-1",
                        "usage": {"input_tokens": 100, "output_tokens": 25},
                    },
                },
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in events), encoding="utf-8")

            output = run_hook_event(home, {"session_id": thread_id, "transcript_path": str(rollout)})

        self.assertEqual(json.loads(output)["systemMessage"].splitlines()[0], "Total: 125 tokens (input 100 / output 25) | Conversation: 125")

    def test_compact_format_keeps_action_line_short(self):
        summary = {
            "task_total_tokens": 100,
            "task_input_tokens": 80,
            "task_output_tokens": 20,
            "conversation_total_tokens": 1000,
            "cache_ratio": 0.5,
            "context": {"tokens": 80, "window": 1000, "ratio": 0.08},
            "task_tool_calls": 2,
            "conversation_tool_calls": 10,
            "cost_label": "N/A",
            "next_action": "Summarize (context is growing)",
        }
        message = format_hook_message(summary)
        self.assertEqual(message.splitlines()[-1], "Cost: N/A | Next: Summarize (context is growing)")


if __name__ == "__main__":
    unittest.main()
