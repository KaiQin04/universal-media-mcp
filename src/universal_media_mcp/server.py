"""FastMCP server entrypoint for universal_media_mcp."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from universal_media_mcp.async_downloads import AsyncDownloadManager
from universal_media_mcp.auth import AuthManager
from universal_media_mcp.config import Settings
from universal_media_mcp.downloader import (
    MetadataDownloader,
    SubtitleDownloader,
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

    metadata = MetadataDownloader(client)
    subtitles = SubtitleDownloader(
        client,
        subtitle_format=settings.subtitle_format,
        max_chars=settings.subtitle_max_chars,
    )
    async_downloads = AsyncDownloadManager(
        client,
        default_video_quality=settings.default_video_quality,
        default_audio_format=settings.default_audio_format,
        default_audio_quality=settings.default_audio_quality,
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
    def start_download(
        url: str,
        quality: str = "best",
        media_type: str = "video",
        audio_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start a background download task (non-blocking).

        Returns a task_id. Call get_download_status to track progress and
        completion.
        """

        return async_downloads.start_download(
            url,
            quality=quality,
            media_type=media_type,
            audio_format=audio_format,
        )

    @mcp.tool()
    def download_video_async(
        url: str,
        quality: str = "best",
    ) -> Dict[str, Any]:
        """Start a background video download task (non-blocking)."""

        return async_downloads.start_download(
            url,
            quality=quality,
            media_type="video",
        )

    @mcp.tool()
    def download_audio_async(
        url: str,
        format: str = "mp3",
        quality: str = "192",
    ) -> Dict[str, Any]:
        """Start a background audio download task (non-blocking)."""

        return async_downloads.start_download(
            url,
            quality=quality,
            media_type="audio",
            audio_format=format,
        )

    @mcp.tool()
    def get_download_status(task_id: str) -> Dict[str, Any]:
        """Get status information for a background download task."""

        return async_downloads.get_download_status(task_id)

    @mcp.tool()
    def list_downloads(status_filter: Optional[str] = None) -> Dict[str, Any]:
        """List background download tasks."""

        return async_downloads.list_downloads(status_filter=status_filter)

    @mcp.tool()
    def cancel_download(task_id: str) -> Dict[str, Any]:
        """Request cancellation of a background download task."""

        return async_downloads.cancel_download(task_id)

    @mcp.tool()
    def wait_for_downloads(
        task_ids: Sequence[str],
        mode: str = "any",
        timeout_seconds: float = 300.0,
    ) -> Dict[str, Any]:
        """Wait for background downloads to complete.

        Use this after starting multiple async downloads to be notified
        when downloads finish, without manual polling.

        Args:
            task_ids: List of task IDs to wait for.
            mode: "any" returns when ANY task completes (recommended for
                  processing downloads as they finish).
                  "all" waits for ALL tasks to complete.
            timeout_seconds: Maximum wait time (default 300 = 5 minutes).

        Returns:
            completed: List of finished task statuses (with file_path).
            pending: List of task IDs still in progress.
            timed_out: True if timeout was reached.

        Example workflow:
            1. Start 5 downloads with download_video_async -> get 5 task_ids
            2. Call wait_for_downloads(task_ids, mode="any")
            3. Process the completed download(s)
            4. Repeat step 2-3 with remaining pending IDs until all done
        """

        return async_downloads.wait_for_downloads(
            list(task_ids),
            mode=mode,
            timeout_seconds=timeout_seconds,
        )

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
