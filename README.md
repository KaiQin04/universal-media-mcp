# Universal Media MCP Server

A Model Context Protocol (MCP) server that provides unified media download tools powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp). Supports 1800+ websites including YouTube, Twitch, Bilibili, Twitter/X, Instagram, and more.

> **Disclaimer**: This project is a thin wrapper around yt-dlp. All download capabilities, supported sites, and media extraction logic are provided by yt-dlp. Please refer to [yt-dlp's documentation](https://github.com/yt-dlp/yt-dlp) for the full list of supported sites and features. Users are responsible for ensuring their use complies with applicable laws and the terms of service of the websites they access.

## Features

- **Video Download** - Download videos in MP4 format with quality selection
- **Audio Download** - Extract audio and convert to MP3 (or other formats via ffmpeg)
- **Async Downloads** - Start background downloads and query progress/status
- **Subtitle Retrieval** - Fetch subtitles with option to save to file or return content directly
- **Metadata Extraction** - Get video metadata without downloading
- **URL Support Check** - Verify if a URL is supported before processing
- **Authentication** - Support for cookies and username/password authentication

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [ffmpeg](https://ffmpeg.org/) (required for audio extraction, format conversion, and merging separate audio/video streams)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-media-mcp.git
cd universal-media-mcp

# Create virtual environment and install dependencies
uv venv
uv sync
```

## Usage

### Running the MCP Server

```bash
uv run universal-media-mcp
```

The server runs via stdio transport and is designed to be integrated with MCP-compatible clients.

### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `check_url_support` | Check if a URL is supported by yt-dlp | `url` |
| `get_metadata` | Extract metadata without downloading | `url` |
| `download_video` | Download video as MP4 | `url`, `quality`, `max_filesize_mb` |
| `download_audio` | Download and convert to audio | `url`, `format`, `quality` |
| `start_download` | Start a background download task | `url`, `quality`, `media_type`, `audio_format` |
| `download_video_async` | Start a background video download task | `url`, `quality` |
| `download_audio_async` | Start a background audio download task | `url`, `format`, `quality` |
| `get_download_status` | Get status for a background download task | `task_id` |
| `list_downloads` | List background download tasks | `status_filter` |
| `cancel_download` | Cancel a background download task | `task_id` |
| `get_subtitles` | Retrieve subtitles | `url`, `languages`, `save_to_file` |

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize as needed:

```bash
# Download directory (default: ~/Downloads/universal_media_mcp)
UNIVERSAL_MEDIA_DOWNLOAD_DIR=/path/to/downloads

# Cookies directory (default: ~/.config/universal_media_mcp/cookies)
UNIVERSAL_MEDIA_COOKIES_DIR=/path/to/cookies

# ffmpeg binary (or containing directory). Helpful for GUI apps with limited PATH.
UNIVERSAL_MEDIA_FFMPEG_LOCATION=/opt/homebrew/bin/ffmpeg

# Platform credentials (optional)
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
BILIBILI_USERNAME=your_username
BILIBILI_PASSWORD=your_password
```

### Cookies Authentication

Place Netscape-format cookie files in the cookies directory:

```
~/.config/universal_media_mcp/cookies/
├── youtube_cookies.txt
├── twitch_cookies.txt
├── bilibili_cookies.txt
├── twitter_cookies.txt
└── instagram_cookies.txt
```

## MCP Client Integration

Replace `<PROJECT_DIR>` with your actual project path.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Edit `~/.claude/settings.json`:

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

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.universal_media]
command = "uv"
args = ["--directory", "<PROJECT_DIR>", "run", "universal-media-mcp"]
```

## Project Structure

```
universal_media_mcp/
├── pyproject.toml
├── .env.example
└── src/
    └── universal_media_mcp/
        ├── __init__.py
        ├── server.py          # FastMCP entry point
        ├── config.py          # Settings management
        ├── auth.py            # Authentication handling
        ├── security.py        # Path validation
        └── downloader/
            ├── base.py        # yt-dlp client wrapper
            ├── video.py       # Video download
            ├── audio.py       # Audio download
            ├── subtitle.py    # Subtitle retrieval
            └── metadata.py    # Metadata extraction
```

## Legal Notice

This software is provided for personal and educational use only. Users must:

1. Comply with the terms of service of websites they access
2. Respect copyright and intellectual property rights
3. Obtain proper authorization before downloading copyrighted content
4. Take full responsibility for their use of this software

The authors and contributors are not responsible for any misuse of this software.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful media downloader that powers this project
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol by Anthropic
- [FastMCP](https://github.com/jlowin/fastmcp) - Fast MCP server framework

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
