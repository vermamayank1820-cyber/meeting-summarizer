"""
Watcher Agent
-------------
Monitors the /recordings directory for new audio/video files using watchdog.
When a new supported file is detected (and has finished writing), it triggers
the processing pipeline via the provided callback.
"""
import time
import threading
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import RECORDINGS_DIR, SUPPORTED_EXTENSIONS

logger = get_logger("WatcherAgent")


class _RecordingEventHandler(FileSystemEventHandler):
    """Internal watchdog handler that filters events and fires the pipeline callback."""

    def __init__(self, on_new_file: Callable[[Path], None], settle_seconds: float = 2.0):
        super().__init__()
        self.on_new_file = on_new_file
        self.settle_seconds = settle_seconds
        self._processing: set = set()

    def _is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTENSIONS

    def _wait_for_file_to_settle(self, path: Path) -> bool:
        """
        Wait until the file size stops changing (i.e., finished writing).
        Returns True if file is ready, False if something went wrong.
        """
        prev_size = -1
        for _ in range(20):  # poll up to 20 times (20 * settle_seconds)
            try:
                curr_size = path.stat().st_size
            except FileNotFoundError:
                return False
            if curr_size == prev_size and curr_size > 0:
                return True
            prev_size = curr_size
            time.sleep(self.settle_seconds)
        return False

    def _handle_path(self, path_str: str):
        path = Path(path_str)
        if not self._is_supported(path):
            return
        if str(path) in self._processing:
            return
        self._processing.add(str(path))

        def _worker():
            logger.info(f"New file detected: {path.name} — waiting for write to complete…")
            if self._wait_for_file_to_settle(path):
                logger.info(f"File ready: {path.name} — triggering pipeline")
                try:
                    self.on_new_file(path)
                except Exception as exc:
                    logger.error(f"Pipeline error for {path.name}: {exc}", exc_info=True)
            else:
                logger.warning(f"File {path.name} never settled — skipping")
            self._processing.discard(str(path))

        threading.Thread(target=_worker, daemon=True).start()

    def on_created(self, event: FileCreatedEvent):
        if not event.is_directory:
            self._handle_path(event.src_path)

    def on_moved(self, event: FileMovedEvent):
        # Handles files moved/saved into the recordings folder
        if not event.is_directory:
            self._handle_path(event.dest_path)


class WatcherAgent:
    """
    Starts a background observer thread watching the recordings folder.
    Calls `on_new_file(path)` for every new supported recording.
    """

    def __init__(self, on_new_file: Callable[[Path], None], watch_dir: Path = RECORDINGS_DIR):
        self.watch_dir = watch_dir
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self._handler = _RecordingEventHandler(on_new_file)
        self._observer = Observer()

    def start(self):
        self._observer.schedule(self._handler, str(self.watch_dir), recursive=False)
        self._observer.start()
        logger.info(f"WatcherAgent started — monitoring: {self.watch_dir}")

    def stop(self):
        self._observer.stop()
        self._observer.join()
        logger.info("WatcherAgent stopped")
