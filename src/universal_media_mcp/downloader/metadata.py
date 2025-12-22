"""Metadata extraction support."""

from __future__ import annotations

from typing import Any, Dict

from universal_media_mcp.downloader.base import YtDlpClient


class MetadataDownloader:
    """Metadata extraction via yt-dlp."""

    def __init__(self, client: YtDlpClient) -> None:
        self._client = client

    def get_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata without downloading."""

        info = self._client.extract_info(
            url,
            download=False,
            extra_options={"skip_download": True},
        )
        return {
            "url": url,
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "channel": info.get("channel"),
            "channel_id": info.get("channel_id"),
            "duration": info.get("duration"),
            "upload_date": info.get("upload_date"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "webpage_url": info.get("webpage_url") or info.get("original_url"),
            "extractor": info.get("extractor"),
            "extractor_key": info.get("extractor_key"),
        }
