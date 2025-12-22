"""Downloader modules built on top of yt-dlp."""

from universal_media_mcp.downloader.audio import AudioDownloader
from universal_media_mcp.downloader.base import YtDlpClient
from universal_media_mcp.downloader.metadata import MetadataDownloader
from universal_media_mcp.downloader.subtitle import SubtitleDownloader
from universal_media_mcp.downloader.video import VideoDownloader

__all__ = [
    "AudioDownloader",
    "MetadataDownloader",
    "SubtitleDownloader",
    "VideoDownloader",
    "YtDlpClient",
]
