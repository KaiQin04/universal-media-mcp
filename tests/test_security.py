import unittest
from pathlib import Path

from universal_media_mcp.security import PathValidator, sanitize_filename


class TestPathValidator(unittest.TestCase):
    def test_ensure_within_allowed_allows_child(self):
        base = Path("/tmp/universal_media_mcp_test_base").resolve()
        validator = PathValidator([base])
        child = base / "a" / "b.txt"
        resolved = validator.ensure_within_allowed(child)
        self.assertTrue(str(resolved).startswith(str(base)))

    def test_ensure_within_allowed_rejects_escape(self):
        base = Path("/tmp/universal_media_mcp_test_base").resolve()
        validator = PathValidator([base])
        with self.assertRaises(ValueError):
            validator.ensure_within_allowed(Path("/tmp").resolve())


class TestSanitizeFilename(unittest.TestCase):
    def test_sanitize_filename_removes_separators(self):
        name = sanitize_filename("../a/b\\c?.txt")
        self.assertNotIn("/", name)
        self.assertNotIn("\\", name)

    def test_sanitize_filename_fallback(self):
        self.assertEqual(sanitize_filename("///"), "file")
