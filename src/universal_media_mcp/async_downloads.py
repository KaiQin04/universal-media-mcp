"""Background download task management for universal_media_mcp."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from universal_media_mcp.downloader.audio import build_audio_postprocessors
from universal_media_mcp.downloader.base import YtDlpClient
from universal_media_mcp.downloader.video import build_video_format_selector


STATUS_PENDING = "pending"
STATUS_DOWNLOADING = "downloading"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELED = "canceled"
STATUS_NOT_FOUND = "not_found"

SUPPORTED_MEDIA_TYPES = ("video", "audio")


class DownloadCancelledError(RuntimeError):
    """Raised when a download task is canceled."""


def utc_now() -> datetime:
    """Return a timezone-aware datetime in UTC."""

    return datetime.now(timezone.utc)


def isoformat_or_none(timestamp: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime to ISO8601, returning None when missing."""

    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.isoformat()


def extract_progress_percent(progress: Mapping[str, Any]) -> Optional[float]:
    """Best-effort percent extraction from a yt-dlp progress hook payload."""

    if progress.get("status") != "downloading":
        return None

    downloaded = progress.get("downloaded_bytes")
    total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
    if not isinstance(downloaded, (int, float)):
        return None
    if not isinstance(total, (int, float)):
        return None
    if total <= 0:
        return None

    percent = (downloaded / total) * 100.0
    if percent < 0:
        return 0.0
    if percent > 100:
        return 100.0
    return percent


@dataclass
class DownloadTask:
    """In-memory representation of a background download task."""

    task_id: str
    url: str
    media_type: str
    quality: str
    audio_format: Optional[str] = None

    status: str = STATUS_PENDING
    progress: float = 0.0

    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    warning: Optional[str] = None

    started_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None

    thread: Optional[threading.Thread] = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    downloaded_files: list[str] = field(default_factory=list)

    def to_status_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable status payload."""

        progress_value = self.progress
        if progress_value < 0:
            progress_value = 0.0
        if progress_value > 100:
            progress_value = 100.0

        is_done = self.status in (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELED)

        return {
            "task_id": self.task_id,
            "url": self.url,
            "media_type": self.media_type,
            "quality": self.quality,
            "status": self.status,
            "is_done": is_done,
            "progress": progress_value,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "error": self.error,
            "warning": self.warning,
            "started_at": isoformat_or_none(self.started_at),
            "completed_at": isoformat_or_none(self.completed_at),
        }


DownloadRunner = Callable[
    [DownloadTask, Callable[[Mapping[str, Any]], None]],
    Tuple[Optional[str], Optional[int]],
]


class AsyncDownloadManager:
    """Manage background media downloads with task tracking."""

    def __init__(
        self,
        client: Optional[YtDlpClient],
        *,
        default_video_quality: str,
        default_audio_format: str,
        default_audio_quality: str,
        download_runner: Optional[DownloadRunner] = None,
    ) -> None:
        self._client = client
        self._default_video_quality = default_video_quality
        self._default_audio_format = default_audio_format
        self._default_audio_quality = default_audio_quality
        self._download_runner = download_runner or self._download_with_ytdlp

        self._tasks: dict[str, DownloadTask] = {}
        self._lock = threading.Lock()

    def start_download(
        self,
        url: str,
        *,
        quality: str = "best",
        media_type: str = "video",
        audio_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start a background download and return a task identifier."""

        normalized_media_type = (media_type or "video").strip().lower()
        if normalized_media_type not in SUPPORTED_MEDIA_TYPES:
            return {
                "task_id": None,
                "status": STATUS_FAILED,
                "url": url,
                "error": (
                    "Unsupported media_type. Expected one of: "
                    f"{', '.join(SUPPORTED_MEDIA_TYPES)}"
                ),
            }

        normalized_quality = (quality or "").strip()
        normalized_audio_format = (audio_format or "").strip().lower()
        if normalized_media_type == "video":
            if not normalized_quality:
                normalized_quality = self._default_video_quality
        else:
            if not normalized_quality or not normalized_quality.isdigit():
                normalized_quality = self._default_audio_quality
            if not normalized_audio_format:
                normalized_audio_format = self._default_audio_format

        task_id = uuid.uuid4().hex
        task = DownloadTask(
            task_id=task_id,
            url=url,
            media_type=normalized_media_type,
            quality=normalized_quality,
            audio_format=normalized_audio_format or None,
        )

        thread = threading.Thread(
            target=self._run_task,
            args=(task_id,),
            daemon=True,
        )
        task.thread = thread

        with self._lock:
            self._tasks[task_id] = task

        thread.start()
        return {
            "task_id": task_id,
            "status": "started",
            "url": url,
            "recommended_poll_seconds": 2,
            "next_action": {
                "tool": "get_download_status",
                "task_id": task_id,
            },
        }

    def get_download_status(self, task_id: str) -> Dict[str, Any]:
        """Return the current status payload for a task."""

        # Read without lock to avoid contention with progress updates.
        task = self._tasks.get(task_id)
        if task is None:
            return {
                "task_id": task_id,
                "status": STATUS_NOT_FOUND,
                "progress": None,
                "file_path": None,
                "file_size": None,
                "error": "Unknown task_id.",
                "started_at": None,
                "completed_at": None,
            }
        return task.to_status_dict()

    def list_downloads(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """List tasks, optionally filtered by status."""

        normalized_filter = None
        if status_filter is not None:
            normalized_filter = status_filter.strip().lower()

        # Read without lock to avoid contention with progress updates.
        tasks = list(self._tasks.values())

        if normalized_filter:
            tasks = [task for task in tasks if task.status == normalized_filter]

        tasks.sort(key=lambda task: task.started_at, reverse=True)
        return {
            "tasks": [task.to_status_dict() for task in tasks],
            "total": len(tasks),
        }

    def cancel_download(self, task_id: str) -> Dict[str, Any]:
        """Request cancellation of a background download."""

        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return {
                    "task_id": task_id,
                    "status": STATUS_NOT_FOUND,
                    "error": "Unknown task_id.",
                }

            if task.status in (
                STATUS_COMPLETED,
                STATUS_FAILED,
                STATUS_CANCELED,
            ):
                return {
                    "task_id": task_id,
                    "status": task.status,
                    "error": None,
                }

            task.cancel_event.set()

            if task.thread is None or not task.thread.is_alive():
                task.status = STATUS_CANCELED
                task.error = "Canceled."
                task.completed_at = utc_now()

        return {"task_id": task_id, "status": "cancel_requested"}

    def _run_task(self, task_id: str) -> None:
        progress_hook = self._build_progress_hook(task_id)
        self._update_task(task_id, status=STATUS_DOWNLOADING, progress=0.0)

        try:
            file_path, file_size = self._execute_download(task_id, progress_hook)
        except DownloadCancelledError as exc:
            self._update_task(
                task_id,
                status=STATUS_CANCELED,
                error=str(exc) or "Canceled.",
                completed_at=utc_now(),
            )
            return
        except Exception as exc:
            file_path, file_size = self._best_effort_primary_file(task_id)
            if file_path:
                self._update_task(
                    task_id,
                    status=STATUS_COMPLETED,
                    progress=100.0,
                    file_path=file_path,
                    file_size=file_size,
                    warning=str(exc),
                    error=None,
                    completed_at=utc_now(),
                )
            else:
                self._update_task(
                    task_id,
                    status=STATUS_FAILED,
                    error=str(exc),
                    warning=None,
                    completed_at=utc_now(),
                )
            return

        self._update_task(
            task_id,
            status=STATUS_COMPLETED,
            progress=100.0,
            file_path=file_path,
            file_size=file_size,
            error=None,
            completed_at=utc_now(),
        )

    def _execute_download(
        self,
        task_id: str,
        progress_hook: Callable[[Mapping[str, Any]], None],
    ) -> Tuple[Optional[str], Optional[int]]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise RuntimeError("Task disappeared.")
            task_copy = DownloadTask(
                task_id=task.task_id,
                url=task.url,
                media_type=task.media_type,
                quality=task.quality,
                audio_format=task.audio_format,
            )
            task_copy.cancel_event = task.cancel_event
            task_copy.downloaded_files = task.downloaded_files
        return self._download_runner(task_copy, progress_hook)

    def _build_progress_hook(
        self,
        task_id: str,
    ) -> Callable[[Mapping[str, Any]], None]:
        def _hook(payload: Mapping[str, Any]) -> None:
            if self._is_cancel_requested(task_id):
                self._best_effort_cleanup_part_files(payload)
                raise DownloadCancelledError("Canceled by user.")

            percent = extract_progress_percent(payload)
            if percent is None:
                if payload.get("status") == "finished":
                    self._update_task(task_id, progress=99.0)
                return

            self._update_task(task_id, progress=min(99.0, percent))

        return _hook

    def _is_cancel_requested(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            return task.cancel_event.is_set()

    def _update_task(
        self,
        task_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error: Optional[str] = None,
        warning: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if file_path is not None:
                task.file_path = file_path
            if file_size is not None:
                task.file_size = file_size
            if error is not None:
                task.error = error
            if warning is not None:
                task.warning = warning
            if completed_at is not None:
                task.completed_at = completed_at

    def _best_effort_primary_file(
        self,
        task_id: str,
    ) -> Tuple[Optional[str], Optional[int]]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None, None
            candidates = list(task.downloaded_files)

        primary = self._choose_primary_file(candidates)
        if primary is None:
            return None, None

        size = None
        try:
            size = Path(primary).stat().st_size
        except OSError:
            size = None
        return primary, size

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

        mp4_candidates = [path for path in candidates if path.suffix.lower() == ".mp4"]
        if mp4_candidates:
            primary = max(mp4_candidates, key=lambda path: path.stat().st_size)
            return str(primary)

        primary = max(candidates, key=lambda path: path.stat().st_size)
        return str(primary)

    def _best_effort_cleanup_part_files(self, payload: Mapping[str, Any]) -> None:
        client = self._client
        if client is None:
            return

        for key in ("tmpfilename", "filename"):
            filename = payload.get(key)
            if not filename:
                continue
            path = Path(str(filename))
            if path.suffix != ".part":
                continue
            try:
                client.safe_unlink(path)
            except Exception:
                continue

    def _download_with_ytdlp(
        self,
        task: DownloadTask,
        progress_hook: Callable[[Mapping[str, Any]], None],
    ) -> Tuple[Optional[str], Optional[int]]:
        client = self._client
        if client is None:
            raise RuntimeError("YtDlpClient not configured.")

        if task.cancel_event.is_set():
            raise DownloadCancelledError("Canceled by user.")

        if task.media_type == "video":
            allow_merge = client.ffmpeg_available()
            extra_options: Dict[str, Any] = {
                "format": build_video_format_selector(
                    task.quality,
                    allow_merge=allow_merge,
                ),
                "progress_hooks": [progress_hook],
            }
            if allow_merge:
                extra_options["merge_output_format"] = "mp4"
        else:
            allow_convert = client.ffmpeg_available()
            audio_format = (task.audio_format or self._default_audio_format).strip()
            audio_quality = (task.quality or self._default_audio_quality).strip()
            extra_options = {
                "format": "bestaudio/best",
                "progress_hooks": [progress_hook],
            }
            if allow_convert:
                extra_options["postprocessors"] = build_audio_postprocessors(
                    audio_format,
                    audio_quality,
                )

        info = client.extract_info(
            task.url,
            download=True,
            extra_options=extra_options,
            downloaded_files=task.downloaded_files,
        )
        file_path = client.best_effort_primary_filepath(info)
        if file_path:
            path = Path(file_path)
            if path.suffix == ".part" or not path.exists():
                file_path = None
        if not file_path:
            file_path = self._choose_primary_file(task.downloaded_files)
        file_size = None
        if file_path:
            try:
                file_size = Path(file_path).stat().st_size
            except OSError:
                file_size = None
        return file_path, file_size

    def check_downloads(
        self,
        task_ids: List[str],
    ) -> Dict[str, Any]:
        """Check current status of downloads (non-blocking).

        Returns immediately with current status of all requested tasks.
        Call repeatedly if you want to poll for completion.

        Args:
            task_ids: List of task IDs to check.

        Returns:
            Dict with completed tasks, pending task IDs, and file paths.
        """
        if not task_ids:
            return {
                "completed": [],
                "pending": [],
                "all_done": True,
                "error": "No task IDs provided.",
            }

        completed_tasks: List[Dict[str, Any]] = []
        pending_list: List[str] = []

        # Read without lock to avoid contention with progress updates.
        # Python GIL ensures dict.get() is atomic.
        for task_id in task_ids:
            task = self._tasks.get(task_id)
            if task is None:
                completed_tasks.append({
                    "task_id": task_id,
                    "status": STATUS_NOT_FOUND,
                    "error": "Unknown task_id.",
                })
                continue

            # Read status once to avoid race conditions
            status = task.status
            if status in (
                STATUS_COMPLETED,
                STATUS_FAILED,
                STATUS_CANCELED,
            ):
                completed_tasks.append(task.to_status_dict())
            else:
                pending_list.append(task_id)

        all_done = len(pending_list) == 0
        completed_paths = [
            t.get("file_path")
            for t in completed_tasks
            if t.get("file_path")
        ]

        if all_done:
            description = f"All {len(completed_tasks)} downloads complete. Process files."
        elif completed_tasks:
            description = (
                f"{len(completed_tasks)} completed, {len(pending_list)} still downloading. "
                "Process completed files or call check_downloads again."
            )
        else:
            description = (
                f"All {len(pending_list)} downloads still in progress. "
                "Call check_downloads again in a few seconds."
            )

        return {
            "completed": completed_tasks,
            "pending": pending_list,
            "all_done": all_done,
            "error": None,
            "next_action": {
                "description": description,
                "pending_task_ids": pending_list,
                "completed_file_paths": completed_paths,
            },
        }
