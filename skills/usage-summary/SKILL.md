---
name: usage-summary
description: Show the compact token, cache, context, tool-call, and next-action summary for the current local Codex conversation. Use when the user asks for current Codex usage or the usage-summary plug-in report.
---

# Usage Summary

Generate the current conversation's usage summary from the local Codex rollout. Never open, print, quote, or summarize raw rollout transcript contents.

On Windows, run:

```powershell
py -3 <plugin-root>\plugin\scripts\usage_hook.py --format compact
```

On macOS or Linux, run:

```bash
python3 <plugin-root>/plugin/scripts/usage_hook.py --format compact
```

Resolve `<plugin-root>` as the directory containing `.codex-plugin/`. The script selects the rollout whose filename matches `CODEX_THREAD_ID`; if this environment variable or matching usage data is unavailable, state that no current-thread summary was found. Never pick the globally newest session as a fallback.

Return the compact report as printed. It includes the latest recorded turn, cumulative selected-conversation totals, cache ratio, latest-turn context pressure, tool-call counts, `Cost: N/A`, and the deterministic next-action recommendation.
