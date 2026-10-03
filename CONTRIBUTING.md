# Contributing

Thank you for your interest in improving Codex Usage Summary. Before submitting a change, open an issue to describe the problem or proposal. Small documentation fixes may go directly into a pull request.

## Development Workflow

1. Fork the repository and create a branch with a clear purpose.
2. Keep changes focused. Do not commit personal Codex rollouts, prompts, tool output, or account data.
3. Run the tests: `python -m unittest discover -s tests -v`.
4. Check Python syntax: `python -m compileall -q source plugin tests`.
5. In the pull request, describe user-visible impact, test results, and any compatibility changes.

This tool parses the local Codex rollout format. If you change schema assumptions, include a minimal fixture that contains no private conversation data and describe which format it covers.
