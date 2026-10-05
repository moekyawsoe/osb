"""Centralized action logging engine adhering to NASA JPL Power of 10 rules.

Provides:
- Thread-safe rotating file logging with static size bounds (Rule 3)
- Real-time Qt signal emission for UI log views
- Bounded memory log history
- Strict function length <= 60 lines and high assertion density (Rule 4 & 5)
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import time
from collections import deque
from typing import Deque, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal

LOG_FILE_NAME = "osb_actions.log"
MAX_LOG_FILE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_LOG_BACKUPS = 3
MAX_MEMORY_LOG_ENTRIES = 1000


class LogSignalEmitter(QObject):
    """Qt signal bridge for real-time log messages."""
    log_emitted = pyqtSignal(str, str, str)  # timestamp, level, message


class ActionLogger:
    """Enterprise logger capturing all system actions, processes, and errors."""

    _instance: Optional["ActionLogger"] = None
    _emitter = LogSignalEmitter()

    def __init__(self, log_dir: Optional[str] = None) -> None:
        """Initialize file and stream logger with static bounds."""
        target_dir = log_dir or os.getcwd()
        assert os.path.exists(target_dir), f"Directory {target_dir} must exist"
        self._log_path = os.path.join(target_dir, LOG_FILE_NAME)
        self._history: Deque[str] = deque(maxlen=MAX_MEMORY_LOG_ENTRIES)

        self._logger = logging.getLogger("OSB_Actions")
        self._logger.setLevel(logging.INFO)
        self._setup_handlers()
        assert len(self._logger.handlers) > 0, "Logger must have at least one handler"

    def _setup_handlers(self) -> None:
        """Attach rotating file handler and console handler with NASA bounds."""
        assert self._logger is not None, "Logger instance required"
        if self._logger.handlers:
            return

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = RotatingFileHandler(
            self._log_path,
            maxBytes=MAX_LOG_FILE_BYTES,
            backupCount=MAX_LOG_BACKUPS,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    @classmethod
    def get_instance(cls) -> "ActionLogger":
        """Singleton accessor for global ActionLogger."""
        if cls._instance is None:
            cls._instance = ActionLogger()
        assert cls._instance is not None, "Instance must exist"
        return cls._instance

    @classmethod
    def get_emitter(cls) -> LogSignalEmitter:
        """Return Qt signal bridge for log updates."""
        assert cls._emitter is not None, "Emitter required"
        return cls._emitter

    def log(self, level: str, source: str, message: str) -> None:
        """Record log entry to file, memory buffer, and emit Qt signal."""
        assert isinstance(level, str) and isinstance(source, str), "Level and source must be strings"
        assert isinstance(message, str), "Message must be string"

        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{source}] {message}"
        lvl_upper = level.upper()

        if lvl_upper == "ERROR":
            self._logger.error(formatted)
        elif lvl_upper == "WARNING":
            self._logger.warning(formatted)
        else:
            self._logger.info(formatted)

        full_record = f"[{ts_str}] [{lvl_upper}] {formatted}"
        self._history.append(full_record)
        self._emitter.log_emitted.emit(ts_str, lvl_upper, formatted)

    def get_history(self) -> List[str]:
        """Return snapshot of memory-buffered log history."""
        records = list(self._history)
        assert isinstance(records, list), "Must return list"
        return records


def log_action(source: str, message: str, level: str = "INFO") -> None:
    """Helper function to log an action easily."""
    assert isinstance(source, str) and len(source) > 0, "Source must be non-empty"
    assert isinstance(message, str), "Message must be string"
    ActionLogger.get_instance().log(level, source, message)


def log_error(source: str, error_message: str) -> None:
    """Helper function to log an error with details."""
    assert isinstance(source, str) and len(source) > 0, "Source must be non-empty"
    assert isinstance(error_message, str), "Error message must be string"
    ActionLogger.get_instance().log("ERROR", source, error_message)
