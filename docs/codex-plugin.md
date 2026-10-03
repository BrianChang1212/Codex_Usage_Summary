# Codex plug-in 安裝

本專案採用 Codex 相容 manifest：`.codex-plugin/plugin.json`，並以 `skills/usage-summary/SKILL.md` 提供手動用量摘要。`hooks/hooks.json` 在每回合停止時呼叫本機彙總程式；不啟動網頁 server。

## Local marketplace 範例

先將本 repo 複製到本機固定路徑，再在 Codex 使用中的 local marketplace 檔案新增 plugin entry。把 `<repository-path>` 換成本機 repo 根目錄的絕對路徑；JSON 字串中的 Windows 反斜線需寫成 `\\`。若已有 marketplace，僅合併 `plugins` 陣列中的項目，不要覆蓋整份檔案。

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

接著在 Codex Plugins 介面選取 `Local Plugins` marketplace 並安裝 `Codex Usage Summary`。安裝後開新 task，Hook 會在回合停止後顯示摘要；也可以呼叫 `usage-summary` Skill 手動查看。

## 使用邊界

- 此為本機 source package，沒有公開發布或自動更新流程。
- 外掛安裝及 Hook 執行依賴本機 project path 持續存在。
- 本 plug-in 有自己的 Stop Hook；若同時啟用既有 Usage Audit Stop Hook，Codex 可能會顯示兩份摘要。
- Hook 僅讀取目前 `CODEX_THREAD_ID` 對應的 rollout，不猜測其他視窗的對話。
- 安裝前請在 Codex plugin interface 檢視其 Skill；僅安裝受信任的本機來源。
