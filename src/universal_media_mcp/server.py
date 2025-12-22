"""FastMCP server entrypoint for universal_media_mcp."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from universal_media_mcp.auth import AuthManager
from universal_media_mcp.config import Settings
from universal_media_mcp.downloader import (
    AudioDownloader,
    MetadataDownloader,
    SubtitleDownloader,
    VideoDownloader,
    YtDlpClient,
)
from universal_media_mcp.security import PathValidator


def create_server() -> Any:
    """Create and configure the FastMCP server instance."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "mcp is required. Install dependencies with `uv sync`."
        ) from exc

    settings = Settings()
    auth_manager = AuthManager(settings.cookies_dir)
    path_validator = PathValidator([settings.download_dir, settings.tmp_dir])
    client = YtDlpClient(
        download_dir=settings.download_dir,
        tmp_dir=settings.tmp_dir,
        auth_manager=auth_manager,
        path_validator=path_validator,
        ffmpeg_location=settings.ffmpeg_location,
    )

    video = VideoDownloader(client)
    audio = AudioDownloader(client)
    metadata = MetadataDownloader(client)
    subtitles = SubtitleDownloader(
        client,
        subtitle_format=settings.subtitle_format,
        max_chars=settings.subtitle_max_chars,
    )

    mcp = FastMCP("universal-media")

    @mcp.tool()
    def check_url_support(url: str) -> Dict[str, Any]:
        """Check whether a URL is supported by yt-dlp extractors."""

        return client.check_url_support(url)

    @mcp.tool()
    def get_metadata(url: str) -> Dict[str, Any]:
        """Extract metadata for a media URL without downloading."""

        return metadata.get_metadata(url)

    @mcp.tool()
    def download_video(
        url: str,
        quality: str = "best",
        max_filesize_mb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Download a video (MP4) from a supported URL."""

        return video.download_video(
            url,
            quality=quality,
            max_filesize_mb=max_filesize_mb,
        )

    @mcp.tool()
    def download_audio(
        url: str,
        format: str = "mp3",
        quality: str = "192",
    ) -> Dict[str, Any]:
        """Download audio and convert with ffmpeg (default: MP3)."""

        return audio.download_audio(url, audio_format=format, quality=quality)

    @mcp.tool()
    def get_subtitles(
        url: str,
        languages: Optional[List[str]] = None,
        save_to_file: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve subtitles for a URL."""

        if save_to_file:
            settings.ensure_directories()
            settings.subtitles_dir.mkdir(parents=True, exist_ok=True)
            return subtitles.get_subtitles(
                url,
                languages=languages,
                save_to_file=True,
                output_dir=settings.subtitles_dir,
            )

        return subtitles.get_subtitles(
            url,
            languages=languages,
            save_to_file=False,
        )

    return mcp


def run() -> None:
    """Run the MCP server with stdio transport."""

    mcp = create_server()
    mcp.run()
