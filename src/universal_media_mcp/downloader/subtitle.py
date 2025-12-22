"""Subtitle retrieval support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from universal_media_mcp.downloader.base import YtDlpClient


def list_available_subtitle_languages(info: Dict[str, Any]) -> List[str]:
    """List available subtitle languages from yt-dlp info dict."""

    languages = set()
    for key in ("subtitles", "automatic_captions"):
        data = info.get(key) or {}
        if isinstance(data, dict):
            languages.update(data.keys())
    return sorted(languages)


def parse_subtitle_filename(
    path: Path,
    *,
    media_id: str,
    subtitle_format: str,
) -> Tuple[Optional[str], str]:
    """Parse language and format from a yt-dlp subtitle filename."""

    name = path.name
    prefix = f"{media_id}."
    suffix = f".{subtitle_format}"
    if name.startswith(prefix) and name.endswith(suffix):
        language = name[len(prefix) : -len(suffix)]
        return language or None, subtitle_format
    return None, subtitle_format


class SubtitleDownloader:
    """Subtitle retrieval via yt-dlp."""

    def __init__(
        self,
        client: YtDlpClient,
        *,
        subtitle_format: str,
        max_chars: int,
    ) -> None:
        self._client = client
        self._subtitle_format = subtitle_format
        self._max_chars = max_chars

    def get_subtitles(
        self,
        url: str,
        *,
        languages: Optional[List[str]] = None,
        save_to_file: bool = False,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Download subtitles and return file paths or contents."""

        target_languages = languages or ["en"]

        if output_dir is None:
            output_dir = (
                self._client.download_dir
                if save_to_file
                else self._client.tmp_dir
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(output_dir / "%(id)s.%(ext)s")
        extra_options = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": target_languages,
            "subtitlesformat": self._subtitle_format,
            "outtmpl": outtmpl,
        }
        info = self._client.extract_info(
            url,
            download=False,
            extra_options=extra_options,
        )
        media_id = info.get("id")
        if not media_id:
            raise ValueError("Missing media id from extracted metadata.")

        available_languages = list_available_subtitle_languages(info)

        pattern = f"{media_id}.*.{self._subtitle_format}"
        subtitle_files = sorted(output_dir.glob(pattern))

        if save_to_file:
            return {
                "url": url,
                "id": media_id,
                "available_languages": available_languages,
                "saved_files": [
                    {
                        "language": parse_subtitle_filename(
                            p,
                            media_id=media_id,
                            subtitle_format=self._subtitle_format,
                        )[0],
                        "format": self._subtitle_format,
                        "path": str(p),
                    }
                    for p in subtitle_files
                ],
            }

        subtitles: List[Dict[str, Any]] = []
        for path in subtitle_files:
            language, subtitle_format = parse_subtitle_filename(
                path,
                media_id=media_id,
                subtitle_format=self._subtitle_format,
            )
            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > self._max_chars:
                content = content[: self._max_chars]
            subtitles.append(
                {
                    "language": language,
                    "format": subtitle_format,
                    "content": content,
                }
            )
            self._client.safe_unlink(path)

        return {
            "url": url,
            "id": media_id,
            "available_languages": available_languages,
            "subtitles": subtitles,
        }
