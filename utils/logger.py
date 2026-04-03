"""
Centralized logging for all agents in the Meeting Summarizer system.
Each agent gets its own named logger that writes to both console and file.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Single log file per day
LOG_FILE = LOG_DIR / f"meeting_summarizer_{datetime.now().strftime('%Y%m%d')}.log"

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger. Creates handlers on first call; reuses on subsequent calls.

    Args:
        name: Logger name (typically the agent class name)

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_FORMATTER)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_FORMATTER)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger
