# Codex Plugin Installation

This project uses the Codex-compatible manifest at `.codex-plugin/plugin.json`. `hooks/hooks.json` runs the local summarizer when each turn stops. No manual command or web server is provided.

## Local Marketplace Example

Choose a local marketplace root and clone this repository into a directory beneath it. Set `source.path` to the plugin directory relative to that marketplace root, starting with `./`; keep the plugin directory inside the marketplace root. For example, if you clone this repository to `<marketplace-root>/plugins/Codex_Usage_Summary`, use `./plugins/Codex_Usage_Summary` below. Replace that example with the relative directory you actually use; do not put a machine-specific absolute path in the marketplace file. If a marketplace file already exists, merge this entry into its `plugins` array instead of replacing the file.

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
        "path": "./plugins/Codex_Usage_Summary"
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
