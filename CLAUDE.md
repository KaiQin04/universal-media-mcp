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
- `wait_for_downloads(task_ids, mode="any", timeout_seconds=300)`：等待下載完成
  - `mode="any"`：任意一個完成就返回（建議用於逐一處理）
  - `mode="all"`：等待全部完成
  - 返回 `completed`（已完成列表）、`pending`（仍在進行的 ID）、`timed_out`

## 建議工作流程

```
1. 啟動多個異步下載 → 取得 task_ids 列表
2. 調用 wait_for_downloads(task_ids, mode="any")
3. 處理已完成的下載（completed 中有 file_path）
4. 用 pending 列表重複步驟 2-3 直到全部完成
```

## 備註

- 任務狀態為記憶體內資料；重啟 MCP server 會清空。
- 狀態值：`pending` / `downloading` / `completed` / `failed` / `canceled`。
