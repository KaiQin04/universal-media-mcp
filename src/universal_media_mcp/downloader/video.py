"""Video download support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from universal_media_mcp.downloader.base import YtDlpClient


def build_video_format_selector(quality: str, *, allow_merge: bool = True) -> str:
    """Build a yt-dlp format selector for MP4 video download."""

    quality = (quality or "best").strip().lower()
    if not allow_merge:
        if quality in ("best", "highest"):
            return "best[ext=mp4]/best"

        if quality.endswith("p") and quality[:-1].isdigit():
            height = int(quality[:-1])
            return (
                "best[ext=mp4][height<="
                f"{height}"
                "]/best[height<="
                f"{height}"
                "]"
            )

        return "best[ext=mp4]/best"

    if quality in ("best", "highest"):
        return (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        )

    if quality.endswith("p") and quality[:-1].isdigit():
        height = int(quality[:-1])
        return (
            "bestvideo[ext=mp4][height<="
            f"{height}"
            "]+bestaudio[ext=m4a]/best[ext=mp4][height<="
            f"{height}"
            "]/best[height<="
            f"{height}"
            "]"
        )

    return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"


class VideoDownloader:
    """Video downloading via yt-dlp."""

    def __init__(self, client: YtDlpClient) -> None:
        self._client = client

    def download_video(
        self,
        url: str,
        *,
        quality: str,
        max_filesize_mb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Download a video and return basic information."""

        allow_merge = self._client.ffmpeg_available()
        downloaded_files: list[str] = []
        extra_options: Dict[str, Any] = {
            "format": build_video_format_selector(quality, allow_merge=allow_merge),
        }
        if allow_merge:
            extra_options["merge_output_format"] = "mp4"
        if max_filesize_mb is not None:
            extra_options["max_filesize"] = int(max_filesize_mb) * 1024 * 1024

        try:
            info = self._client.extract_info(
                url,
                download=True,
                extra_options=extra_options,
                downloaded_files=downloaded_files,
            )
        except Exception as exc:
            primary = self._choose_primary_file(downloaded_files)
            if primary is None:
                raise

            metadata = self._best_effort_metadata(url)
            ext = metadata.get("ext")
            if not ext:
                ext = Path(primary).suffix.lstrip(".") or None

            return {
                "url": url,
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "ext": ext,
                "duration": metadata.get("duration"),
                "webpage_url": metadata.get("webpage_url")
                or metadata.get("original_url")
                or url,
                "file_path": primary,
                "downloaded_files": downloaded_files,
                "ffmpeg_available": allow_merge,
                "warning": str(exc),
            }

        filepath = self._client.best_effort_primary_filepath(info)

        result: Dict[str, Any] = {
            "url": url,
            "id": info.get("id"),
            "title": info.get("title"),
            "ext": info.get("ext"),
            "duration": info.get("duration"),
            "webpage_url": info.get("webpage_url") or info.get("original_url"),
            "file_path": filepath,
            "ffmpeg_available": allow_merge,
        }
        if not allow_merge:
            result["warning"] = (
                "ffmpeg not available; downloaded a single-file format without "
                "merging audio/video streams."
            )
        return result

    def _best_effort_metadata(self, url: str) -> Dict[str, Any]:
        try:
            return self._client.extract_info(
                url,
                download=False,
                extra_options={"skip_download": True},
            )
        except Exception:
            return {}

    @staticmethod
    def _choose_primary_file(downloaded_files: list[str]) -> Optional[str]:
        candidates = []
        for filename in downloaded_files:
            path = Path(filename)
            if path.suffix == ".part":
                continue
            if not path.exists():
                continue
            candidates.append(path)

        if not candidates:
            return None

        mp4_candidates = [p for p in candidates if p.suffix.lower() == ".mp4"]
        if mp4_candidates:
            largest_mp4 = max(mp4_candidates, key=lambda p: p.stat().st_size)
            return str(largest_mp4)

        largest = max(candidates, key=lambda p: p.stat().st_size)
        return str(largest)
