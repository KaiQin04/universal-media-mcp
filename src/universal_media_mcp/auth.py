"""Authentication helpers for yt-dlp."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional, Tuple
from urllib.parse import urlparse


PLATFORM_COOKIE_FILES = {
    "youtube": "youtube_cookies.txt",
    "twitch": "twitch_cookies.txt",
    "bilibili": "bilibili_cookies.txt",
    "twitter": "twitter_cookies.txt",
    "instagram": "instagram_cookies.txt",
}


def detect_platform(url: str) -> Optional[str]:
    """Best-effort platform detection from URL host."""

    host = (urlparse(url).netloc or "").lower()
    host = host.split("@")[-1]
    if host.startswith("www."):
        host = host[4:]

    if host.endswith(("youtube.com", "youtu.be")):
        return "youtube"
    if host.endswith("twitch.tv"):
        return "twitch"
    if host.endswith("bilibili.com"):
        return "bilibili"
    if host.endswith(("twitter.com", "x.com")):
        return "twitter"
    if host.endswith("instagram.com"):
        return "instagram"
    return None


class AuthManager:
    """Build authentication-related yt-dlp options based on URL."""

    def __init__(
        self,
        cookies_dir: Path,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._cookies_dir = cookies_dir.expanduser()
        self._env = dict(env) if env is not None else dict(os.environ)

    @property
    def cookies_dir(self) -> Path:
        """Base directory for per-platform cookie files."""

        return self._cookies_dir

    def get_cookiefile(self, url: str) -> Optional[Path]:
        """Return cookie file path if it exists for the URL's platform."""

        platform = detect_platform(url)
        if not platform:
            return None
        filename = PLATFORM_COOKIE_FILES.get(platform)
        if not filename:
            return None
        candidate = self._cookies_dir / filename
        if candidate.exists():
            return candidate
        return None

    def get_credentials(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Return (username, password) from env vars for the URL's platform."""

        platform = detect_platform(url)
        if not platform:
            return None, None

        prefix = platform.upper()
        username = self._env.get(f"{prefix}_USERNAME")
        password = self._env.get(f"{prefix}_PASSWORD")
        if username and password:
            return username, password
        return None, None

    def build_ytdlp_auth_options(self, url: str) -> dict:
        """Build yt-dlp options for cookies and login credentials."""

        options: dict = {}
        cookiefile = self.get_cookiefile(url)
        if cookiefile:
            options["cookiefile"] = str(cookiefile)

        username, password = self.get_credentials(url)
        if username and password:
            options["username"] = username
            options["password"] = password

        return options
