"""Dual-panel browser container with central transfer action bar.

Complies with NASA JPL Power of 10 rules.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from osb.core.models import TransferOperation
from osb.core.rclone_cli import RcloneCli
from osb.core.transfer_mgr import TransferManager
from osb.gui.outline_icons import OutlineIcons
from osb.gui.panel_browser import PanelBrowser


class DualPanelWidget(QWidget):
    """Container holding left and right storage panels with central transfer actions."""

    def __init__(
        self,
        cli: RcloneCli,
        transfer_mgr: TransferManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        assert cli is not None, "CLI executor required"
        assert transfer_mgr is not None, "TransferManager required"
        self._cli = cli
        self._mgr = transfer_mgr
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize dual panel layout with splitter and middle control strip."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        self._left_panel = PanelBrowser(self._cli, "Source Panel", parent=self)
        self._splitter.addWidget(self._left_panel)

        # Center transfer action bar
        center_bar = self._create_center_bar()
        self._splitter.addWidget(center_bar)

        # Right panel
        self._right_panel = PanelBrowser(self._cli, "Destination Panel", parent=self)
        self._splitter.addWidget(self._right_panel)

        self._splitter.setStretchFactor(0, 10)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setStretchFactor(2, 10)

        main_layout.addWidget(self._splitter)

    def _create_center_bar(self) -> QWidget:
        """Construct central transfer button strip."""
        bar = QWidget()
        bar.setMaximumWidth(90)
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(2, 40, 2, 40)
        layout.setSpacing(10)
        layout.addStretch()

        copy_lr_btn = QPushButton("Copy")
        copy_lr_btn.setIcon(OutlineIcons.get_icon("arrow_right"))
        copy_lr_btn.setToolTip("Copy selected items from Left to Right")
        copy_lr_btn.clicked.connect(lambda: self._trigger_transfer(TransferOperation.COPY, True))
        layout.addWidget(copy_lr_btn)

        copy_rl_btn = QPushButton("Copy")
        copy_rl_btn.setIcon(OutlineIcons.get_icon("arrow_left"))
        copy_rl_btn.setToolTip("Copy selected items from Right to Left")
        copy_rl_btn.clicked.connect(lambda: self._trigger_transfer(TransferOperation.COPY, False))
        layout.addWidget(copy_rl_btn)

        move_lr_btn = QPushButton("Move")
        move_lr_btn.setIcon(OutlineIcons.get_icon("move"))
        move_lr_btn.setToolTip("Move selected items from Left to Right")
        move_lr_btn.clicked.connect(lambda: self._trigger_transfer(TransferOperation.MOVE, True))
        layout.addWidget(move_lr_btn)

        move_rl_btn = QPushButton("Move")
        move_rl_btn.setIcon(OutlineIcons.get_icon("move"))
        move_rl_btn.setToolTip("Move selected items from Right to Left")
        move_rl_btn.clicked.connect(lambda: self._trigger_transfer(TransferOperation.MOVE, False))
        layout.addWidget(move_rl_btn)

        sync_btn = QPushButton("Sync")
        sync_btn.setIcon(OutlineIcons.get_icon("sync"))
        sync_btn.setToolTip("Synchronize directories (Left -> Right)")
        sync_btn.clicked.connect(self._trigger_sync)
        layout.addWidget(sync_btn)

        layout.addStretch()
        return bar

    def _trigger_transfer(self, op: TransferOperation, left_to_right: bool) -> None:
        """Queue transfer job for selected items."""
        src_panel = self._left_panel if left_to_right else self._right_panel
        dst_panel = self._right_panel if left_to_right else self._left_panel

        items = src_panel.get_selected_items()
        if not items:
            QMessageBox.information(self, "Selection Required", "Please select items to transfer.")
            return

        src_remote = src_panel.get_current_remote()
        dst_remote = dst_panel.get_current_remote()
        dst_path = dst_panel.get_current_path()

        if not dst_remote:
            QMessageBox.warning(self, "Destination Required", "Please select a destination remote.")
            return

        # Queue jobs for selected items
        for it in items:
            sub_dst = f"{dst_path}/{it.name}".lstrip("/") if dst_path else it.name
            self._mgr.submit_job(op, src_remote, it.path, dst_remote, sub_dst)

    def _trigger_sync(self) -> None:
        """Trigger directory synchronization from Left to Right."""
        src_remote = self._left_panel.get_current_remote()
        src_path = self._left_panel.get_current_path()
        dst_remote = self._right_panel.get_current_remote()
        dst_path = self._right_panel.get_current_path()

        if not src_remote or not dst_remote:
            QMessageBox.warning(self, "Sync Incomplete", "Both source and destination must be selected.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Sync",
            f"Are you sure you want to synchronize:\n{src_remote}:{src_path}\n->\n{dst_remote}:{dst_path}\n"
            "Warning: Destination files missing in source may be overwritten!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._mgr.submit_job(TransferOperation.SYNC, src_remote, src_path, dst_remote, dst_path)

    def set_remotes(self, remotes: List[str]) -> None:
        """Distribute remotes to both left and right panels."""
        assert isinstance(remotes, list), "Remotes must be a list"
        self._left_panel.set_remotes(remotes)
        self._right_panel.set_remotes(remotes)
        if len(remotes) > 1:
            self._right_panel.select_remote(remotes[1])

    def refresh_panels(self) -> None:
        """Refresh both explorer views."""
        self._left_panel.refresh()
        self._right_panel.refresh()

    def close_panels(self) -> None:
        """Close child panels cleanly."""
        assert self._left_panel is not None and self._right_panel is not None, "Panels required"
        self._left_panel.close()
        self._right_panel.close()

