"""Common yt-dlp wrapper logic."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from universal_media_mcp.auth import AuthManager
from universal_media_mcp.security import PathValidator


_COMMON_FFMPEG_LOCATIONS = (
    Path("/opt/homebrew/bin/ffmpeg"),
    Path("/usr/local/bin/ffmpeg"),
    Path("/usr/bin/ffmpeg"),
)


class YtDlpClient:
    """A small wrapper around yt-dlp to standardize options and outputs."""

    def __init__(
        self,
        download_dir: Path,
        tmp_dir: Path,
        auth_manager: AuthManager,
        path_validator: PathValidator,
        ffmpeg_location: Optional[Path] = None,
    ) -> None:
        self._download_dir = download_dir
        self._tmp_dir = tmp_dir
        self._auth_manager = auth_manager
        self._path_validator = path_validator
        self._ffmpeg_location = self._resolve_ffmpeg_location(ffmpeg_location)

    @property
    def download_dir(self) -> Path:
        """Directory for downloaded media files."""

        return self._download_dir

    @property
    def tmp_dir(self) -> Path:
        """Directory for temporary intermediate files."""

        return self._tmp_dir

    @property
    def ffmpeg_location(self) -> Optional[Path]:
        """Resolved ffmpeg binary (or directory) location if available."""

        return self._ffmpeg_location

    def ffmpeg_available(self) -> bool:
        """Return True if ffmpeg looks available for yt-dlp post-processing."""

        location = self._ffmpeg_location
        if location is None:
            return False

        location = location.expanduser()
        if location.is_dir():
            return (location / "ffmpeg").exists()
        return location.exists()

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""

        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    def check_url_support(self, url: str) -> Dict[str, Any]:
        """Check if a URL looks supported by yt-dlp without network calls."""

        self._import_yt_dlp()
        from yt_dlp.extractor import gen_extractors  # type: ignore

        generic_match = None
        for extractor in gen_extractors():
            try:
                if extractor.suitable(url):
                    if extractor.IE_NAME == "generic":
                        generic_match = extractor.IE_NAME
                        continue
                    return {"supported": True, "extractor": extractor.IE_NAME}
            except Exception:
                continue

        if generic_match is not None:
            return {"supported": True, "extractor": generic_match}

        return {"supported": False, "extractor": None}

    def extract_info(
        self,
        url: str,
        *,
        download: bool,
        extra_options: Optional[Mapping[str, Any]] = None,
        downloaded_files: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Extract metadata and optionally download media for a URL."""

        self.ensure_directories()
        options: Dict[str, Any] = self._build_base_options(url)
        if extra_options:
            options.update(dict(extra_options))

        if downloaded_files is not None:
            downloaded_files_set: set[str] = set()

            def _progress_hook(status: Dict[str, Any]) -> None:
                if status.get("status") != "finished":
                    return

                filename = status.get("filename")
                if not filename:
                    return

                filename_str = str(filename)
                if filename_str in downloaded_files_set:
                    return

                downloaded_files_set.add(filename_str)
                downloaded_files.append(filename_str)

            hooks = options.get("progress_hooks") or []
            if not isinstance(hooks, list):
                hooks = list(hooks)
            hooks.append(_progress_hook)
            options["progress_hooks"] = hooks

        yt_dlp = self._import_yt_dlp()
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=download)
        return info

    def best_effort_primary_filepath(
        self,
        info: Mapping[str, Any],
    ) -> Optional[str]:
        """Best-effort extraction of the downloaded file path."""

        requested = info.get("requested_downloads") or []
        if isinstance(requested, list) and requested:
            filepath = requested[0].get("filepath")
            if filepath:
                return str(filepath)

        for key in ("filepath", "_filename"):
            filepath = info.get(key)
            if filepath:
                return str(filepath)

        media_id = info.get("id")
        if not media_id:
            return None

        candidates = sorted(
            self._download_dir.glob(f"*{media_id}*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return str(candidates[0])

        return None

    def safe_unlink(self, path: Path) -> None:
        """Delete a file if it is in an allowed directory."""

        self._path_validator.safe_unlink(path)

    def _build_base_options(self, url: str) -> Dict[str, Any]:
        outtmpl = str(self._download_dir / "%(title)s-%(id)s.%(ext)s")
        options: Dict[str, Any] = {
            "outtmpl": outtmpl,
            "paths": {
                "home": str(self._download_dir),
                "temp": str(self._tmp_dir),
            },
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        if self._ffmpeg_location is not None:
            options["ffmpeg_location"] = str(self._ffmpeg_location)
        options.update(self._auth_manager.build_ytdlp_auth_options(url))
        return options

    @staticmethod
    def _resolve_ffmpeg_location(
        explicit: Optional[Path],
    ) -> Optional[Path]:
        if explicit is not None:
            candidate = explicit.expanduser()
            if candidate.exists():
                return candidate

        which_path = shutil.which("ffmpeg")
        if which_path:
            return Path(which_path)

        for candidate in _COMMON_FFMPEG_LOCATIONS:
            if candidate.exists():
                return candidate

        return None

    @staticmethod
    def _import_yt_dlp() -> Any:
        try:
            import yt_dlp
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "yt-dlp is required. Install dependencies with `uv sync`."
            ) from exc
        return yt_dlp
