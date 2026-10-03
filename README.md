# Codex Usage Summary

A local Codex plug-in that displays a compact three-line usage summary after each turn. It shows task and conversation token totals, cache, context, tool calls, cost status, and a recommended next action. There is no manual command, web UI, HTTP server, or outbound runtime network request.

## Installation

Requirements: Codex plug-in support, Windows/macOS/Linux, and Python 3.10+. Clone the repository from GitHub and install it through a Codex local marketplace. See [`docs/codex-plugin.md`](docs/codex-plugin.md) for instructions. After installing **Codex Usage Summary**, start a new task to load the Stop Hook.

Review and trust the local command in the Codex hooks interface before enabling the Stop Hook. If the existing Codex Usage Audit Stop Hook is also enabled, both hooks will display a summary. Disable either hook to avoid duplicate summaries.

## Example Output

```text
Total: 10.2K tokens (input 9.8K / output 400) | Conversation: 23.5K
Cache: 75.0% | Context: 25.0% (64K / 256K) | Tools: task 7 / conversation 21
Cost: N/A | Next: Summarize (context is growing)
```

The values above are illustrative.

This version does not include a pricing table, so it displays `Cost: N/A`. Recommendations use explicit thresholds and may suggest `Summarize`, `Start fresh`, or `Split task` as context usage or task scope grows.

## Data Sources and Privacy

- The Hook prefers the `transcript_path` supplied by the Codex Stop event and does not guess which conversation is globally newest.
- Rollouts are stored under `sessions/` or `archived_sessions/` in `CODEX_HOME` (`%USERPROFILE%\.codex` or `~/.codex` if unset). The plug-in reads only the selected local rollout, line by line.
- Output contains only aggregate numbers and recommendations. It does not include prompts, responses, tool names, arguments, or tool output.
- The plug-in does not modify rollout files, write parsing caches, start a server, or make network requests.
- Sub-agent sessions are not included in cumulative conversation totals.
- Missing usage records are not estimated. The Hook silently skips the summary if it cannot find the current thread.

## Repository Structure

```text
20261003_Codex_Usage_Summary/
├── .codex-plugin/plugin.json
├── hooks/hooks.json
├── plugin/scripts/usage_hook.py
├── source/token_usage.py
├── source/usage_summary.py
├── tests/
└── docs/
```

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).

## Contributing and Security Reports

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution guidelines. Report security issues privately as described in [`SECURITY.md`](SECURITY.md). Do not post rollouts or conversation data in public issues.
