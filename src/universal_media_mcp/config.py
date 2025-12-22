"""Application configuration for universal_media_mcp."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Missing dependencies. Install with `uv sync` before running."
    ) from exc


class Settings(BaseSettings):
    """Settings loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_prefix="UNIVERSAL_MEDIA_",
        env_file=".env",
        extra="ignore",
    )

    download_dir: Path = Field(
        default_factory=lambda: (
            Path.home() / "Downloads" / "universal_media_mcp"
        )
    )
    cookies_dir: Path = Field(
        default_factory=lambda: Path.home()
        / ".config"
        / "universal_media_mcp"
        / "cookies"
    )
    tmp_dir: Path = Field(
        default_factory=lambda: (
            Path.home() / ".cache" / "universal_media_mcp" / "tmp"
        )
    )
    ffmpeg_location: Optional[Path] = None

    subtitle_format: str = "vtt"
    subtitle_max_chars: int = 500_000

    default_video_quality: str = "best"
    default_audio_format: str = "mp3"
    default_audio_quality: str = "192"

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""

        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def subtitles_dir(self) -> Path:
        """Directory for persisted subtitle files."""

        return self.download_dir / "subtitles"
