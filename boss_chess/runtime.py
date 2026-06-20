from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
from typing import Callable

from boss_chess.app_paths import LOG_FILE, crashes_dir, ensure_app_dirs, logs_dir


LOGGER_NAME = "boss_chess"


def configure_logging() -> logging.Logger:
    ensure_app_dirs()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    log_path = logs_dir() / LOG_FILE
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)
    return logger


def install_exception_hooks(logger: logging.Logger, gui_reporter: Callable[[str, BaseException], None] | None = None) -> None:
    def _handle_exception(exc_type, exc_value, exc_tb: TracebackType | None) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            return sys.__excepthook__(exc_type, exc_value, exc_tb)
        message = _format_exception(exc_type, exc_value, exc_tb)
        logger.error(message)
        _write_crash_report(message)
        if gui_reporter is not None:
            try:
                gui_reporter("Boss Chess crashed", exc_value)
            except Exception:
                pass

    sys.excepthook = _handle_exception


def _format_exception(exc_type, exc_value, exc_tb: TracebackType | None) -> str:
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))


def _write_crash_report(message: str) -> Path:
    ensure_app_dirs()
    path = crashes_dir() / f"crash-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.txt"
    path.write_text(message, encoding="utf-8")
    return path
