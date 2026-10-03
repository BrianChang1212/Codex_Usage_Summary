# Usage Data and Calculation

The Stop Hook reads `transcript_path` and `session_id` from the Codex hook event. It verifies that the path is under `sessions/` or `archived_sessions/` within `CODEX_HOME` (defaults to `%USERPROFILE%\\.codex` or `~/.codex`). It reads only the current thread and does not combine sub-agent sessions.

## Summary Scope

- Task usage: the latest turn with token usage in the selected rollout.
- Conversation usage: cumulative usage across all recorded turns in the selected rollout.
- Cache ratio: cached input divided by input for the latest turn.
- Context ratio: the largest recorded request input in the latest turn divided by the model context window. Displays `N/A` when the window is unavailable.
- Tool calls: events in `response_item` whose type ends in `_call`, deduplicated by call ID. Only the count is reported.
- Cost: always `N/A` because no rates are configured.
- Next action: `Continue`, `Summarize`, `Start fresh`, or `Split task`, based on context, turn/token, and tool-call thresholds.

## Event Priority

1. New format, `token_usage_record.payload.usage`: each record represents one model response and is deduplicated by `response_id`.
2. Legacy format, `event_msg` with `payload.type == token_count`: reads `payload.info.last_token_usage`; cumulative `total_token_usage` is not treated as per-turn usage.
3. If both formats describe the same response, `token_usage_record` takes precedence. Matching legacy duplicates are removed using the turn and token field values.

Only values recorded in the rollout are used. Missing usage, an unparsable trailing line, or an unknown schema is not estimated. If `total_tokens` is missing or zero, it is calculated as input plus output. Cached input and reasoning output are subsets of input and output, respectively, and are not counted twice. Cache writes are reported separately and are not added again to input or total.

## Privacy Boundary

The Hook outputs only a three-line summary as a Codex `systemMessage`. Raw JSONL text is not included in Hook output, extra logs, or disk caches. The Hook does not modify Codex rollouts, start an HTTP server, or make runtime network requests.
