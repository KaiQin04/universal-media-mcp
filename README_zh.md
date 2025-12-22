# Universal Media MCP Server

一個基於 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的 Model Context Protocol (MCP) 伺服器，提供統一的媒體下載工具介面。支援 YouTube、Twitch、Bilibili、Twitter/X、Instagram 等 1800+ 網站。

> **免責聲明**：本專案僅是 yt-dlp 的薄封裝層 (thin wrapper)。所有下載功能、支援網站及媒體擷取邏輯均由 yt-dlp 提供。完整的支援網站列表與功能說明請參閱 [yt-dlp 官方文件](https://github.com/yt-dlp/yt-dlp)。使用者須自行確保其使用方式符合相關法律及所存取網站之服務條款。

## 功能

- **影片下載** - 下載 MP4 格式影片，支援畫質選擇
- **音訊下載** - 擷取音訊並轉換為 MP3（或透過 ffmpeg 轉換為其他格式）
- **字幕擷取** - 取得字幕，可選擇存檔或直接回傳內容
- **Metadata 擷取** - 不下載即可取得影片資訊
- **URL 支援檢查** - 在處理前確認 URL 是否被支援
- **認證機制** - 支援 Cookies 與帳號密碼認證

## 系統需求

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)（建議）或 pip
- [ffmpeg](https://ffmpeg.org/)（音訊擷取、格式轉換、以及合併分離的影音串流必需）

## 安裝

```bash
# 複製專案
git clone https://github.com/yourusername/universal-media-mcp.git
cd universal-media-mcp

# 建立虛擬環境並安裝依賴
uv venv
uv sync
```

## 使用方式

### 執行 MCP Server

```bash
uv run universal-media-mcp
```

伺服器透過 stdio 傳輸運行，設計用於與 MCP 相容的客戶端整合。

### MCP 工具

| 工具 | 說明 | 參數 |
|------|------|------|
| `check_url_support` | 檢查 URL 是否被 yt-dlp 支援 | `url` |
| `get_metadata` | 不下載直接擷取 metadata | `url` |
| `download_video` | 下載 MP4 影片 | `url`, `quality`, `max_filesize_mb` |
| `download_audio` | 下載並轉換為音訊 | `url`, `format`, `quality` |
| `get_subtitles` | 擷取字幕 | `url`, `languages`, `save_to_file` |

## 設定

### 環境變數

將 `.env.example` 複製為 `.env` 並依需求調整：

```bash
# 下載目錄（預設：~/Downloads/universal_media_mcp）
UNIVERSAL_MEDIA_DOWNLOAD_DIR=/path/to/downloads

# Cookies 目錄（預設：~/.config/universal_media_mcp/cookies）
UNIVERSAL_MEDIA_COOKIES_DIR=/path/to/cookies

# ffmpeg 執行檔（或所在目錄）。GUI App 的 PATH 不完整時可用此指定。
UNIVERSAL_MEDIA_FFMPEG_LOCATION=/opt/homebrew/bin/ffmpeg

# 平台帳號密碼（選用）
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
BILIBILI_USERNAME=your_username
BILIBILI_PASSWORD=your_password
```

### Cookies 認證

將 Netscape 格式的 cookie 檔案放置於 cookies 目錄：

```
~/.config/universal_media_mcp/cookies/
├── youtube_cookies.txt
├── twitch_cookies.txt
├── bilibili_cookies.txt
├── twitter_cookies.txt
└── instagram_cookies.txt
```

## MCP 客戶端整合

請將 `<PROJECT_DIR>` 替換為實際的專案路徑。

### Claude Desktop

編輯 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "universal-media": {
      "command": "uv",
      "args": ["--directory", "<PROJECT_DIR>", "run", "universal-media-mcp"]
    }
  }
}
```

### Claude Code

編輯 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "universal-media": {
      "command": "uv",
      "args": ["--directory", "<PROJECT_DIR>", "run", "universal-media-mcp"]
    }
  }
}
```

### Codex

編輯 `~/.codex/config.toml`：

```toml
[mcp_servers.universal_media]
command = "uv"
args = ["--directory", "<PROJECT_DIR>", "run", "universal-media-mcp"]
```

## 專案結構

```
universal_media_mcp/
├── pyproject.toml
├── .env.example
└── src/
    └── universal_media_mcp/
        ├── __init__.py
        ├── server.py          # FastMCP 入口點
        ├── config.py          # 設定管理
        ├── auth.py            # 認證處理
        ├── security.py        # 路徑驗證
        └── downloader/
            ├── base.py        # yt-dlp 客戶端封裝
            ├── video.py       # 影片下載
            ├── audio.py       # 音訊下載
            ├── subtitle.py    # 字幕擷取
            └── metadata.py    # Metadata 擷取
```

## 法律聲明

本軟體僅供個人及教育用途。使用者必須：

1. 遵守所存取網站之服務條款
2. 尊重著作權與智慧財產權
3. 在下載受版權保護的內容前取得適當授權
4. 對使用本軟體之行為負完全責任

作者與貢獻者不對本軟體之任何濫用行為負責。

## 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案。

```
MIT License

Copyright (c) 2025

特此免費授予任何取得本軟體及相關文件檔案（以下稱「軟體」）副本之人，
不受限制地處理本軟體之權利，包括但不限於使用、複製、修改、合併、
發布、散佈、再授權及/或販售本軟體之副本，並允許被提供本軟體之人
在符合下列條件下從事上述行為：

上述版權聲明及本許可聲明應包含於本軟體之所有副本或重要部分中。

本軟體係按「現狀」提供，不附帶任何明示或暗示之擔保，包括但不限於
適銷性、特定用途適用性及不侵權之擔保。在任何情況下，作者或版權
持有人均不對因本軟體或使用或其他處理本軟體而產生或與之相關的任何
索賠、損害或其他責任負責，無論是在合約、侵權或其他訴訟中。
```

## 致謝

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 驅動本專案的強大媒體下載器
- [MCP](https://modelcontextprotocol.io/) - Anthropic 的 Model Context Protocol
- [FastMCP](https://github.com/jlowin/fastmcp) - 快速 MCP 伺服器框架

## 貢獻

歡迎貢獻！請隨時提交 Pull Request。
