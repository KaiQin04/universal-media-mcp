"""Audio download support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from universal_media_mcp.downloader.base import YtDlpClient


def build_audio_postprocessors(audio_format: str, quality: str) -> list[dict]:
    """Build yt-dlp postprocessors for extracting audio with ffmpeg."""

    audio_format = (audio_format or "mp3").strip().lower()
    quality = (quality or "192").strip()
    return [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": quality,
        }
    ]


class AudioDownloader:
    """Audio downloading via yt-dlp."""

    def __init__(self, client: YtDlpClient) -> None:
        self._client = client

    def download_audio(
        self,
        url: str,
        *,
        audio_format: str,
        quality: str,
    ) -> Dict[str, Any]:
        """Download audio and return basic information."""

        allow_convert = self._client.ffmpeg_available()
        downloaded_files: list[str] = []
        extra_options: Dict[str, Any] = {"format": "bestaudio/best"}
        if allow_convert:
            extra_options["postprocessors"] = build_audio_postprocessors(
                audio_format,
                quality,
            )

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

            ext = Path(primary).suffix.lstrip(".") or None
            return {
                "url": url,
                "id": None,
                "title": None,
                "ext": ext,
                "duration": None,
                "webpage_url": url,
                "file_path": primary,
                "downloaded_files": downloaded_files,
                "ffmpeg_available": allow_convert,
                "warning": str(exc),
            }

        filepath = self._client.best_effort_primary_filepath(info)
        ext = audio_format if allow_convert else info.get("ext")
        result: Dict[str, Any] = {
            "url": url,
            "id": info.get("id"),
            "title": info.get("title"),
            "ext": ext,
            "duration": info.get("duration"),
            "webpage_url": info.get("webpage_url") or info.get("original_url"),
            "file_path": filepath,
            "ffmpeg_available": allow_convert,
        }
        if not allow_convert:
            result["warning"] = (
                "ffmpeg not available; downloaded original audio without "
                "format conversion."
            )
        return result

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

        largest = max(candidates, key=lambda p: p.stat().st_size)
        return str(largest)
