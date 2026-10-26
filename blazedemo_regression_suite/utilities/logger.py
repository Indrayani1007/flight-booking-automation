"""
Logger utility for BlazeDemo Regression Suite.

Provides a colorized StreamHandler for console output and a
RotatingFileHandler that writes to reports/test_run.log.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.config import cfg


# ---------------------------------------------------------------------------
# ANSI color codes — used only when the terminal supports them
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_COLORS: dict[int, str] = {
    logging.DEBUG:    "\033[36m",   # Cyan
    logging.INFO:     "\033[32m",   # Green
    logging.WARNING:  "\033[33m",   # Yellow
    logging.ERROR:    "\033[31m",   # Red
    logging.CRITICAL: "\033[35m",   # Magenta
}


class _ColorFormatter(logging.Formatter):
    """Custom formatter that prepends ANSI color codes for terminal output."""

    _FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    _DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, use_color: bool = True) -> None:
        super().__init__(fmt=self._FMT, datefmt=self._DATE_FMT)
        self._use_color = use_color and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if self._use_color:
            color = _COLORS.get(record.levelno, _RESET)
            return f"{color}{message}{_RESET}"
        return message


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

_registry: dict[str, logging.Logger] = {}


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Return a named logger configured with:
    - A colorized StreamHandler (stdout).
    - A RotatingFileHandler writing to cfg.log_file (10 MB, 5 backups).

    Repeated calls with the same ``name`` return the cached instance.

    Args:
        name:  Logger name (typically ``__name__`` of the caller module).
        level: Minimum log level (default DEBUG).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    if name in _registry:
        return _registry[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # prevent double-logging to root

    # --- Console handler ---------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(_ColorFormatter(use_color=True))
    logger.addHandler(console_handler)

    # --- File handler ------------------------------------------------------
    log_path: Path = cfg.log_file
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(_ColorFormatter(use_color=False))
    logger.addHandler(file_handler)

    _registry[name] = logger
    return logger
