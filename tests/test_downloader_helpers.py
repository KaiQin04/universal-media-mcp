import unittest
from pathlib import Path

from universal_media_mcp.downloader.audio import build_audio_postprocessors
from universal_media_mcp.downloader.subtitle import parse_subtitle_filename
from universal_media_mcp.downloader.video import build_video_format_selector


class TestBuildVideoFormatSelector(unittest.TestCase):
    def test_best(self):
        selector = build_video_format_selector("best")
        self.assertIn("bestvideo", selector)

    def test_best_no_merge(self):
        selector = build_video_format_selector("best", allow_merge=False)
        self.assertNotIn("bestvideo", selector)
        self.assertIn("best[ext=mp4]", selector)

    def test_height(self):
        selector = build_video_format_selector("720p")
        self.assertIn("height<=720", selector)

    def test_height_no_merge(self):
        selector = build_video_format_selector("720p", allow_merge=False)
        self.assertNotIn("bestvideo", selector)
        self.assertIn("height<=720", selector)


class TestBuildAudioPostprocessors(unittest.TestCase):
    def test_build_audio_postprocessors(self):
        processors = build_audio_postprocessors("mp3", "192")
        self.assertIsInstance(processors, list)
        self.assertEqual(processors[0]["preferredcodec"], "mp3")
        self.assertEqual(processors[0]["preferredquality"], "192")


class TestParseSubtitleFilename(unittest.TestCase):
    def test_parse_subtitle_filename(self):
        language, subtitle_format = parse_subtitle_filename(
            Path("abc.en.vtt"),
            media_id="abc",
            subtitle_format="vtt",
        )
        self.assertEqual(language, "en")
        self.assertEqual(subtitle_format, "vtt")

    def test_parse_subtitle_filename_mismatch(self):
        language, subtitle_format = parse_subtitle_filename(
            Path("other.en.vtt"),
            media_id="abc",
            subtitle_format="vtt",
        )
        self.assertIsNone(language)
        self.assertEqual(subtitle_format, "vtt")
