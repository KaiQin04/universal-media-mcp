import threading
import unittest

from universal_media_mcp.async_downloads import (
    AsyncDownloadManager,
    DownloadCancelledError,
    STATUS_CANCELED,
    STATUS_COMPLETED,
    STATUS_NOT_FOUND,
    extract_progress_percent,
)


class TestExtractProgressPercent(unittest.TestCase):
    def test_returns_none_for_non_downloading(self):
        percent = extract_progress_percent(
            {
                "status": "finished",
                "downloaded_bytes": 10,
                "total_bytes": 100,
            }
        )
        self.assertIsNone(percent)

    def test_returns_none_when_missing_bytes(self):
        percent = extract_progress_percent({"status": "downloading"})
        self.assertIsNone(percent)

    def test_uses_total_bytes(self):
        percent = extract_progress_percent(
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes": 200,
            }
        )
        self.assertEqual(percent, 25.0)

    def test_uses_total_bytes_estimate(self):
        percent = extract_progress_percent(
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes_estimate": 100,
            }
        )
        self.assertEqual(percent, 50.0)


class TestAsyncDownloadManager(unittest.TestCase):
    def test_start_download_completes(self):
        def runner(task, progress_hook):
            progress_hook(
                {
                    "status": "downloading",
                    "downloaded_bytes": 1,
                    "total_bytes": 4,
                }
            )
            progress_hook({"status": "finished", "filename": "dummy.mp4"})
            return "dummy.mp4", 123

        manager = AsyncDownloadManager(
            None,
            default_video_quality="best",
            default_audio_format="mp3",
            default_audio_quality="192",
            download_runner=runner,
        )
        response = manager.start_download(
            "https://example.com/video",
            quality="best",
            media_type="video",
        )
        task_id = response["task_id"]
        manager._tasks[task_id].thread.join(timeout=2)

        status = manager.get_download_status(task_id)
        self.assertEqual(status["status"], STATUS_COMPLETED)
        self.assertEqual(status["progress"], 100.0)
        self.assertEqual(status["file_path"], "dummy.mp4")
        self.assertEqual(status["file_size"], 123)
        self.assertIsNotNone(status["started_at"])
        self.assertIsNotNone(status["completed_at"])

    def test_cancel_unknown_task(self):
        manager = AsyncDownloadManager(
            None,
            default_video_quality="best",
            default_audio_format="mp3",
            default_audio_quality="192",
            download_runner=lambda *_: (None, None),
        )
        response = manager.cancel_download("missing")
        self.assertEqual(response["status"], STATUS_NOT_FOUND)

    def test_cancel_running_task(self):
        started = threading.Event()

        def runner(task, progress_hook):
            started.set()
            task.cancel_event.wait(timeout=2)
            raise DownloadCancelledError("Canceled by user.")

        manager = AsyncDownloadManager(
            None,
            default_video_quality="best",
            default_audio_format="mp3",
            default_audio_quality="192",
            download_runner=runner,
        )
        response = manager.start_download(
            "https://example.com/video",
            quality="best",
            media_type="video",
        )
        task_id = response["task_id"]
        self.assertTrue(started.wait(timeout=1))

        manager.cancel_download(task_id)
        manager._tasks[task_id].thread.join(timeout=2)

        status = manager.get_download_status(task_id)
        self.assertEqual(status["status"], STATUS_CANCELED)

    def test_list_downloads_with_status_filter(self):
        def runner(task, progress_hook):
            return "dummy.mp4", 123

        manager = AsyncDownloadManager(
            None,
            default_video_quality="best",
            default_audio_format="mp3",
            default_audio_quality="192",
            download_runner=runner,
        )
        task_ids = [
            manager.start_download(f"https://example.com/{idx}")["task_id"]
            for idx in range(2)
        ]
        for task_id in task_ids:
            manager._tasks[task_id].thread.join(timeout=2)

        response = manager.list_downloads(status_filter=STATUS_COMPLETED)
        self.assertEqual(response["total"], 2)
        self.assertTrue(
            all(task["status"] == STATUS_COMPLETED for task in response["tasks"])
        )
