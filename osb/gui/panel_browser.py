"""Single object storage browser panel.

Complies with NASA JPL Power of 10 rules.
"""

import os
from typing import List, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


from osb.core.constants import MAX_ITEMS_PER_DIR
from osb.core.models import StorageItem
from osb.core.rclone_cli import RcloneCli
from osb.core.utils import format_bytes
from osb.gui.bucket_dialog import BucketPropertiesDialog, CreateBucketDialog
from osb.gui.file_details_dialog import FileDetailsDialog
from osb.gui.outline_icons import OutlineIcons


class ListWorker(QThread):
    """Background worker to list remote or bucket directory contents."""
    items_ready = pyqtSignal(bool, list, str)

    def __init__(self, cli: RcloneCli, remote: str, path: str) -> None:
        super().__init__()
        assert cli is not None, "CLI required"
        assert isinstance(remote, str) and isinstance(path, str), "Remote and path must be strings"
        self._cli = cli
        self._remote = remote
        self._path = path

    def run(self) -> None:
        """Fetch items using rclone."""
        res = self._cli.list_items(self._remote, self._path)
        if res.success and isinstance(res.data, list):
            self.items_ready.emit(True, res.data, "")
        else:
            self.items_ready.emit(False, [], res.message)


class PanelBrowser(QWidget):
    """Explorer panel for browsing and managing files in a remote or local storage."""

    path_changed = pyqtSignal(str, str)  # remote, path

    def __init__(self, cli: RcloneCli, panel_title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        assert cli is not None, "CLI executor required"
        assert len(panel_title) > 0, "Panel title required"
        self._cli = cli
        self._title = panel_title
        self._current_remote = ""
        self._current_path = ""
        self._items: List[StorageItem] = []
        self._worker: Optional[ListWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Set up browser widgets."""
        assert self._cli is not None, "CLI executor required"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        layout.addLayout(self._create_nav_row())
        layout.addLayout(self._create_actions_row())

        self._table = self._create_table_widget()
        layout.addWidget(self._table)

        self.setMinimumWidth(260)
        self._status_label = QLabel("Ready")
        self._status_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._status_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        layout.addWidget(self._status_label)
        assert self._table is not None, "Table must be initialized"


    def _create_nav_row(self) -> QHBoxLayout:
        """Create navigation row with remote selector and path edit."""
        row = QHBoxLayout()
        self._remote_combo = QComboBox()
        self._remote_combo.setMinimumWidth(140)
        self._remote_combo.currentIndexChanged.connect(self._on_remote_selected)
        row.addWidget(self._remote_combo)

        up_btn = QPushButton()
        up_btn.setIcon(OutlineIcons.get_icon("arrow_up"))
        up_btn.setToolTip("Up to parent folder / bucket")
        up_btn.clicked.connect(self.navigate_up)
        row.addWidget(up_btn)

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("/bucket or /bucket/prefix")
        self._path_edit.returnPressed.connect(self._on_path_entered)
        row.addWidget(self._path_edit)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(OutlineIcons.get_icon("refresh"))
        refresh_btn.setToolTip("Refresh current view")
        refresh_btn.clicked.connect(self.refresh)
        row.addWidget(refresh_btn)
        return row

    def _create_actions_row(self) -> QHBoxLayout:
        """Create action buttons and search filter bar."""
        act_row = QHBoxLayout()
        new_btn = QPushButton("New")
        new_btn.setIcon(OutlineIcons.get_icon("folder_plus"))
        new_btn.clicked.connect(self._on_new_folder_or_bucket)
        act_row.addWidget(new_btn)

        del_btn = QPushButton("Delete")
        del_btn.setIcon(OutlineIcons.get_icon("trash"))
        del_btn.clicked.connect(self._delete_selected)
        act_row.addWidget(del_btn)

        prop_btn = QPushButton("Properties")
        prop_btn.setIcon(OutlineIcons.get_icon("info"))
        prop_btn.clicked.connect(self._show_selected_properties)
        act_row.addWidget(prop_btn)

        act_row.addStretch()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter...")
        self._search_edit.setMaximumWidth(150)
        self._search_edit.textChanged.connect(self._filter_table)
        act_row.addWidget(self._search_edit)
        return act_row

    def _create_table_widget(self) -> QTableWidget:
        """Construct storage items table widget."""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Name", "Size", "Modified", "Type"])
        h = table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.doubleClicked.connect(self._on_table_double_click)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_context_menu)
        return table


    def set_remotes(self, remotes: List[str]) -> None:
        """Populate the remote selector combo box."""
        assert isinstance(remotes, list), "Remotes must be a list"
        self._remote_combo.blockSignals(True)
        self._remote_combo.clear()
        for r in remotes:
            self._remote_combo.addItem(r)
        self._remote_combo.blockSignals(False)

        if remotes:
            self._current_remote = remotes[0]
            self.refresh()

    def select_remote(self, remote_name: str) -> None:
        """Switch active remote programmatically."""
        idx = self._remote_combo.findText(remote_name)
        if idx >= 0:
            self._remote_combo.setCurrentIndex(idx)

    def _on_remote_selected(self, index: int) -> None:
        """Handle remote switch."""
        self._current_remote = self._remote_combo.currentText()
        self._current_path = ""
        self._path_edit.setText("")
        self.refresh()

    def _on_path_entered(self) -> None:
        """Handle path manual input."""
        self._current_path = self._path_edit.text().strip("/")
        self.refresh()

    def navigate_up(self) -> None:
        """Navigate to parent folder or bucket root."""
        if not self._current_path:
            return
        parts = self._current_path.split("/")
        parts.pop()
        self._current_path = "/".join(parts)
        self._path_edit.setText(self._current_path)
        self.refresh()

    def set_status_message(self, text: str, is_error: bool = False) -> None:
        """Update status line safely without expanding parent widget size."""
        assert isinstance(text, str), "Status text must be string"
        assert self._status_label is not None, "Status label required"
        short_txt = (text[:90] + "...") if len(text) > 90 else text
        self._status_label.setText(short_txt)
        self._status_label.setToolTip(text if len(text) > 90 else "")
        color = "#f87171" if is_error else "#9ca3af"
        self._status_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def refresh(self) -> None:
        """Reload contents of current remote and path."""
        assert self._cli is not None, "CLI executor required"
        if not self._current_remote:
            return

        if self._worker and self._worker.isRunning():
            self._worker.wait(200)

        self.set_status_message(f"Loading {self._current_remote}:{self._current_path}...")
        self._worker = ListWorker(self._cli, self._current_remote, self._current_path)
        self._worker.items_ready.connect(self._on_items_loaded)
        self._worker.start()

    def closeEvent(self, event) -> None:
        """Safely terminate background listing workers upon widget closure."""
        assert event is not None, "Close event cannot be None"
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(300)
        super().closeEvent(event)

    def _on_items_loaded(self, success: bool, items: list, err: str) -> None:
        """Populate table with fetched items."""
        assert self._table is not None, "Table cannot be None"
        self._table.setRowCount(0)
        self._items = items if success else []

        if not success:
            self.set_status_message(f"Error: {err}", is_error=True)
            return

        bound_count = min(len(self._items), MAX_ITEMS_PER_DIR)
        for i in range(bound_count):
            item = self._items[i]
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Name with outline icon
            icon_type = "bucket" if item.is_bucket else ("folder" if item.is_dir else "file")
            name_cell = QTableWidgetItem(OutlineIcons.get_icon(icon_type), item.name)
            self._table.setItem(row, 0, name_cell)

            size_str = "<DIR>" if item.is_dir else format_bytes(item.size)
            self._table.setItem(row, 1, QTableWidgetItem(size_str))
            self._table.setItem(row, 2, QTableWidgetItem(item.mod_time[:19] if item.mod_time else "--"))
            type_str = "Bucket" if item.is_bucket else ("Folder" if item.is_dir else (item.mime_type or "File"))
            self._table.setItem(row, 3, QTableWidgetItem(type_str))

        self.set_status_message(f"{len(self._items)} item(s) in {self._current_remote}:{self._current_path or '/'}")
        self.path_changed.emit(self._current_remote, self._current_path)


    def _on_table_double_click(self) -> None:
        """Enter folder or bucket upon double click."""
        row = self._table.currentRow()
        if row < 0 or row >= len(self._items):
            return
        item = self._items[row]
        if item.is_dir:
            self._current_path = item.path
            self._path_edit.setText(self._current_path)
            self.refresh()
        else:
            self._show_selected_properties()

    def _filter_table(self, query: str) -> None:
        """Filter table rows based on search text."""
        assert self._table is not None, "Table cannot be None"
        term = query.strip().lower()
        for r in range(self._table.rowCount()):
            item = self._table.item(r, 0)
            text = item.text().lower() if item else ""
            self._table.setRowHidden(r, term not in text if term else False)

    def _show_context_menu(self, pos) -> None:
        """Display right-click context menu."""
        menu = QMenu(self)
        sel_items = self.get_selected_items()

        if sel_items and len(sel_items) == 1 and sel_items[0].is_dir:
            open_act = menu.addAction(OutlineIcons.get_icon("folder"), "Open")
            open_act.triggered.connect(self._on_table_double_click)

        prop_act = menu.addAction(OutlineIcons.get_icon("info"), "Properties / Details")
        prop_act.triggered.connect(self._show_selected_properties)

        del_act = menu.addAction(OutlineIcons.get_icon("trash"), "Delete")
        del_act.triggered.connect(self._delete_selected)

        menu.addSeparator()
        new_act = menu.addAction(OutlineIcons.get_icon("folder_plus"), "New Folder / Bucket")
        new_act.triggered.connect(self._on_new_folder_or_bucket)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_new_folder_or_bucket(self) -> None:
        """Create bucket at root or folder in current prefix."""
        assert self._cli is not None, "CLI executor required"
        if not self._current_path:
            # Bucket creation at remote root
            dlg = CreateBucketDialog(self._current_remote, parent=self)
            if dlg.exec() == CreateBucketDialog.DialogCode.Accepted:
                bname = dlg.get_bucket_name()
                res = self._cli.make_bucket_or_dir(self._current_remote, bname)
                if res.success:
                    self.refresh()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to create bucket: {res.message}")
        else:
            # Folder creation
            name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
            if ok and name.strip():
                new_path = f"{self._current_path}/{name.strip()}"
                res = self._cli.make_bucket_or_dir(self._current_remote, new_path)
                if res.success:
                    self.refresh()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to create folder: {res.message}")

    def _delete_selected(self) -> None:
        """Delete selected files or directories."""
        items = self.get_selected_items()
        if not items:
            QMessageBox.information(self, "Selection", "Please select items to delete.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to permanently delete {len(items)} selected item(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        for it in items:
            self._cli.delete_item(self._current_remote, it.path, is_dir=it.is_dir, purge=True)
        self.refresh()

    def _show_selected_properties(self) -> None:
        """Show property inspector dialog for selected item."""
        items = self.get_selected_items()
        if not items:
            return
        it = items[0]
        if it.is_bucket:
            dlg = BucketPropertiesDialog(self._current_remote, it.name, self._cli, parent=self)
            dlg.exec()
        else:
            dlg = FileDetailsDialog(it, self._current_remote, self._cli, parent=self)
            dlg.exec()

    def get_selected_items(self) -> List[StorageItem]:
        """Return list of StorageItems currently selected."""
        selected_rows = set(index.row() for index in self._table.selectedIndexes())
        res: List[StorageItem] = []
        for r in selected_rows:
            if r < len(self._items):
                res.append(self._items[r])
        return res

    def get_current_remote(self) -> str:
        """Return currently selected remote name."""
        return self._current_remote

    def get_current_path(self) -> str:
        """Return current path in browser."""
        return self._current_path
