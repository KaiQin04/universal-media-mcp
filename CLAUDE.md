# 開發備忘

- 依賴管理：`uv`
- MCP 入口：`universal_media_mcp/server.py`
- 環境變數範例：`.env.example`

## 非同步下載工具

- `start_download(url, quality="best", media_type="video")`：啟動背景下載並回傳 `task_id`
- `get_download_status(task_id)`：查詢任務狀態與進度（含 `file_path` / `file_size`）
- `list_downloads(status_filter=None)`：列出任務清單（可用狀態篩選）
- `cancel_download(task_id)`：請求取消進行中的任務

## 備註

- 任務狀態為記憶體內資料；重啟 MCP server 會清空。
- 狀態值：`pending` / `downloading` / `completed` / `failed` / `canceled`。
