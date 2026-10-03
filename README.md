# Codex Usage Summary

本機 Codex plug-in，仿照目前 Usage Audit 的回合結束摘要：顯示最新 task token、conversation 累積量、cache、context、tool calls、費用狀態與下一步建議。Stop Hook 自動顯示；也可用 `usage-summary` Skill 手動呼叫。無網頁 UI、HTTP server 或外部 runtime 網路請求。

## 安裝

需求：Codex plug-in 支援、Windows/macOS/Linux、Python 3.9+。本專案目前是 local marketplace package，安裝設定見 [`docs/codex-plugin.md`](docs/codex-plugin.md)。將 project 根目錄加入個人 local marketplace 後，在 Codex Plugins 安裝 **Codex Usage Summary**，開新 task 載入 Skill 與 Hook。

Stop Hook 需要在 Codex hooks 介面檢視並信任本機 command。若既有 Codex Usage Audit Stop Hook 同時啟用，會顯示兩份摘要；停用其中一個 Hook 可避免重複。

## 顯示格式

```text
Total: 10.2K tokens (input 9.8K / output 400) | Conversation: 23.5K
Cache: 75.0% | Context: 25.0% (64K / 256K) | Tools: task 7 / conversation 21
Cost: N/A | Next: Summarize (context is growing)
```

本版本未整合費率卡，因此顯示 `Cost: N/A`。建議沿用明確門檻規則；context 或 task 廣度增加時會顯示 Summarize、Start fresh 或 Split task。

## 資料來源與隱私

- Hook 優先讀取 Codex Stop event 指定的 `transcript_path`；手動 Skill 依 `CODEX_THREAD_ID` 在檔名中定位。兩種方式都不猜測全域最新 conversation。
- Rollout 位於 `CODEX_HOME`（未設定則 `%USERPROFILE%\.codex` 或 `~/.codex`）的 `sessions/` 或 `archived_sessions/`，只逐行讀取目前選中的本機 rollout。
- 輸出只有彙總數字與建議，不輸出 prompt、回覆、工具名稱、參數或工具輸出。
- 不修改 rollout 檔案、不寫解析快取、不啟動 server、不連外。
- 子 agent session 不併入 conversation 累積量。
- 對沒有 usage 記錄的 turn 不補估數字；找不到目前 thread 時 Hook 安靜略過。

## 專案結構

```text
20261003_Codex_Usage_Summary/
├── .codex-plugin/plugin.json
├── hooks/hooks.json
├── plugin/scripts/usage_hook.py
├── skills/usage-summary/SKILL.md
├── source/token_usage.py
├── source/usage_summary.py
├── tests/
└── docs/
```
