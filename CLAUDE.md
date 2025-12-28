# 開發備忘

- 依賴管理：`uv`
- MCP 入口：`universal_media_mcp/server.py`
- 環境變數範例：`.env.example`

## 非同步下載工具

- `start_download(url, quality="best", media_type="video")`：啟動背景下載並回傳 `task_id`
- `download_video_async(url, quality="best")`：啟動背景影片下載（建議優先使用）
- `download_audio_async(url, format="mp3", quality="192")`：啟動背景音訊下載（建議優先使用）
- `get_download_status(task_id)`：查詢任務狀態與進度（含 `file_path` / `file_size`）
- `list_downloads(status_filter=None)`：列出任務清單（可用狀態篩選）
- `cancel_download(task_id)`：請求取消進行中的任務
- `check_downloads(task_ids)`：檢查下載狀態（非阻塞，立即返回）
  - 返回 `completed`（已完成列表，含 file_path）
  - 返回 `pending`（仍在下載的 task_id 列表）
  - 返回 `all_done`（布林值，全部完成為 true）

## 建議工作流程

```
1. 啟動多個異步下載 → 取得 task_ids 列表
2. 調用 check_downloads(task_ids)
3. 處理 completed 中的下載（有 file_path）
4. 若 pending 不為空，稍後再調用 check_downloads
5. 重複步驟 2-4 直到 all_done = true
```

## 備註

- 任務狀態為記憶體內資料；重啟 MCP server 會清空。
- 狀態值：`pending` / `downloading` / `completed` / `failed` / `canceled`。
