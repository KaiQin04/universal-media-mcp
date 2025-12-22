import unittest
from pathlib import Path

from universal_media_mcp.auth import AuthManager, detect_platform


class TestDetectPlatform(unittest.TestCase):
    def test_detect_platform_common_hosts(self):
        self.assertEqual(
            detect_platform("https://www.youtube.com/watch?v=1"),
            "youtube",
        )
        self.assertEqual(detect_platform("https://youtu.be/1"), "youtube")
        self.assertEqual(
            detect_platform("https://twitch.tv/someone"),
            "twitch",
        )
        self.assertEqual(
            detect_platform("https://www.bilibili.com/video/1"),
            "bilibili",
        )
        self.assertEqual(
            detect_platform("https://x.com/user/status/1"),
            "twitter",
        )
        self.assertEqual(
            detect_platform("https://instagram.com/p/1"),
            "instagram",
        )


class TestAuthManager(unittest.TestCase):
    def test_build_ytdlp_auth_options_uses_credentials(self):
        env = {"TWITTER_USERNAME": "u", "TWITTER_PASSWORD": "p"}
        manager = AuthManager(Path("/tmp/does-not-exist"), env=env)
        options = manager.build_ytdlp_auth_options(
            "https://x.com/user/status/1",
        )
        self.assertEqual(options.get("username"), "u")
        self.assertEqual(options.get("password"), "p")
