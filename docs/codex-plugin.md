# Codex Plugin Installation

This project uses the Codex-compatible manifest at `.codex-plugin/plugin.json`. `hooks/hooks.json` runs the local summarizer when each turn stops. No manual command or web server is provided.

## Local Marketplace Example

Clone this repository to a stable local path, then add the plugin entry to the local marketplace file used by Codex. Replace `<repository-path>` with the absolute path to the repository root. Escape Windows backslashes as `\\` in the JSON string. If a marketplace file already exists, merge this entry into its `plugins` array instead of replacing the file.

```json
{
  "name": "local-plugins",
  "interface": {
    "displayName": "Local Plugins"
  },
  "plugins": [
    {
      "name": "codex-usage-summary",
      "source": {
        "source": "local",
        "path": "<repository-path>"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

In the Codex Plugins interface, select the `Local Plugins` marketplace and install `Codex Usage Summary`. Start a new task after installation; the Hook will display a summary after each turn stops.

## Usage Notes

- This is a local source package with no automated publishing or update workflow.
- The local repository path must remain available for the plugin and Hook to run.
- This plugin has its own Stop Hook. If the Codex Usage Audit Stop Hook is also enabled, Codex may display two summaries.
- The Hook reads the current rollout specified by the Stop event and does not guess which conversation belongs to another window.
- Review the Hook command in the Codex plugin interface before installation, and install only from a trusted source.
