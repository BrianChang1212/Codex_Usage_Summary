# 貢獻指南

感謝你有意改善 Codex Usage Summary。提交變更前請先開 issue 說明問題或提案；小型文件修正可直接提交 pull request。

## 開發流程

1. Fork repo 並建立用途明確的分支。
2. 保持變更聚焦，避免提交個人 Codex rollout、prompt、工具輸出或帳戶資料。
3. 執行測試：`python -m unittest discover -s tests -v`。
4. 檢查 Python 語法：`python -m compileall -q source plugin tests`。
5. Pull request 說明使用者可見影響、測試結果與任何相容性變化。

此工具解析 Codex 本機 rollout 格式；若修改 schema 假設，請附上不含私人對話內容的最小 fixture，並說明適用格式。
