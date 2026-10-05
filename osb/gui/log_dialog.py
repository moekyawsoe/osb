"""Action logging viewer dialog displaying real-time system and process telemetry.

Complies with NASA JPL Power of 10 rules.
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from osb.core.logger import ActionLogger
from osb.gui.outline_icons import OutlineIcons


class ActionLogsDialog(QDialog):
    """Real-time console displaying all application actions, commands, and errors."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = ActionLogger.get_instance()
        assert self._logger is not None, "Logger instance required"
        self._init_ui()
        self._load_history()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Construct the action logs window."""
        self.setWindowTitle("Action Process Logs")
        self.resize(750, 480)
        self.setWindowIcon(OutlineIcons.get_icon("terminal"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addLayout(self._create_toolbar_layout())

        self._text_area = QTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setStyleSheet(
            "background-color: #111215; color: #d1d5db; font-family: monospace; font-size: 11px;"
        )
        layout.addWidget(self._text_area)

        layout.addLayout(self._create_bottom_layout())
        assert self._text_area is not None, "Text area initialized"

    def _create_toolbar_layout(self) -> QHBoxLayout:
        """Construct filter bar and action buttons."""
        top_bar = QHBoxLayout()
        title_lbl = QLabel("SYSTEM ACTION PROCESSES")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #9ca3af;")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["ALL", "INFO", "WARNING", "ERROR"])
        self._filter_combo.currentIndexChanged.connect(self._apply_filter)
        top_bar.addWidget(self._filter_combo)

        clear_btn = QPushButton("Clear View")
        clear_btn.setIcon(OutlineIcons.get_icon("trash"))
        clear_btn.clicked.connect(self._clear_view)
        top_bar.addWidget(clear_btn)
        return top_bar

    def _create_bottom_layout(self) -> QHBoxLayout:
        """Construct bottom action bar."""
        bot_bar = QHBoxLayout()
        path_lbl = QLabel(f"Log Destination: {self._logger._log_path}")
        path_lbl.setStyleSheet("color: #6b7280; font-size: 10px;")
        bot_bar.addWidget(path_lbl)
        bot_bar.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setIcon(OutlineIcons.get_icon("cross"))
        close_btn.clicked.connect(self.accept)
        bot_bar.addWidget(close_btn)
        return bot_bar

    def _connect_signals(self) -> None:
        """Listen to live log messages from ActionLogger."""
        assert self._logger is not None, "Logger must be present"
        ActionLogger.get_emitter().log_emitted.connect(self._on_live_log)

    def _load_history(self) -> None:
        """Populate initial text from bounded memory buffer."""
        assert self._text_area is not None, "Text area required"
        history = self._logger.get_history()
        for line in history:
            self._text_area.append(line)
        self._scroll_to_bottom()

    def _on_live_log(self, ts: str, level: str, msg: str) -> None:
        """Append live log event to view."""
        assert isinstance(ts, str) and isinstance(level, str), "Types must be string"
        curr_filter = self._filter_combo.currentText()
        if curr_filter != "ALL" and level != curr_filter:
            return

        line = f"[{ts}] [{level}] {msg}"
        self._text_area.append(line)
        self._scroll_to_bottom()

    def _apply_filter(self) -> None:
        """Reload text with active level filter applied."""
        assert self._text_area is not None, "Text area required"
        self._text_area.clear()
        target = self._filter_combo.currentText()
        for line in self._logger.get_history():
            if target == "ALL" or f"[{target}]" in line:
                self._text_area.append(line)
        self._scroll_to_bottom()

    def _clear_view(self) -> None:
        """Clear current text display."""
        assert self._text_area is not None, "Text area required"
        self._text_area.clear()

    def _scroll_to_bottom(self) -> None:
        """Auto-scroll log viewer to the latest line."""
        cursor = self._text_area.textCursor()
        cursor.movePosition(cursor.MoveMode.End)
        self._text_area.setTextCursor(cursor)
