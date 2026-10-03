# 用量資料與計算方式

Stop Hook 讀取 Codex hook event 提供的 `transcript_path` 與 `session_id`，並確認路徑在 `CODEX_HOME`（未設定時使用 `%USERPROFILE%\.codex` 或 `~/.codex`）底下的 `sessions/` 或 `archived_sessions/`。手動摘要依 `CODEX_THREAD_ID` 在檔名中定位。只讀取目前 thread，不合併 sub-agent session。

## 摘要範圍

- Task 用量：所選 rollout 中最新一個有 token usage 的 turn。
- Conversation 用量：所選 rollout 所有已記錄 turn 的累積量。
- Cache ratio：最新 turn cached input ÷ input。
- Context ratio：最新 turn 中已記錄 request 的最大 input ÷ model context window；缺少 window 時顯示 `N/A`。
- Tool calls：`response_item` 中型別以 `_call` 結尾的事件，依 call ID 去重；只輸出數量。
- Cost：未配置費率，固定為 `N/A`。
- Next：依最新 context、turn/token 與 tool-call 門檻回傳 Continue、Summarize、Start fresh 或 Split task。

## 事件優先序

1. 新格式 `token_usage_record.payload.usage`：每筆代表一個模型回應，使用 `response_id` 去重。
2. 舊格式 `event_msg` 且 `payload.type == token_count`：使用 `payload.info.last_token_usage`；不把累計性的 `total_token_usage` 當成單回合用量。
3. 同一回應同時有兩種格式時，以 `token_usage_record` 為主，依 turn 與 token 欄位值去掉對應的舊格式副本。

只採用 rollout 已記錄的數值。缺少 usage、無法解析的尾端行或未知 schema 不會補估。`total_tokens` 欄位缺少或為零時，以 input + output 計算。Cache input 與 reasoning output 分別是 input/output 的子集，不重複加總；cache write 獨立呈現，不再加入 input 或 total。

## 隱私邊界

Hook 只將三行摘要輸出為 Codex `systemMessage`；原始 JSONL 文字不進入 hook 輸出、額外 log 或磁碟快取。Hook 不修改 Codex rollout、不啟動 HTTP server，也不進行 runtime 網路呼叫。
