"""Object details and metadata inspection dialog.

Complies with NASA JPL Power of 10 rules.
"""

from typing import Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from osb.core.models import StorageItem
from osb.core.rclone_cli import RcloneCli
from osb.core.utils import format_bytes
from osb.gui.outline_icons import OutlineIcons


class HashWorker(QThread):
    """Worker to compute object hash asynchronously."""
    hash_ready = pyqtSignal(str)

    def __init__(self, cli: RcloneCli, remote: str, path: str, hash_type: str = "md5") -> None:
        super().__init__()
        assert cli is not None, "CLI must not be None"
        assert len(remote) > 0, "Remote must be non-empty"
        self._cli = cli
        self._remote = remote
        self._path = path
        self._hash_type = hash_type

    def run(self) -> None:
        """Compute hash and emit result."""
        assert self._cli is not None, "CLI must be active"
        res = self._cli.get_hash(self._remote, self._path, self._hash_type)
        val = str(res.data) if res.success else "Unavailable"
        self.hash_ready.emit(val)


class FileDetailsDialog(QDialog):
    """Clean enterprise dialog displaying object storage metadata and hash."""

    def __init__(
        self,
        item: StorageItem,
        remote: str,
        cli: RcloneCli,
        parent: Optional[QDialog] = None,
    ) -> None:
        super().__init__(parent)
        assert isinstance(item, StorageItem), "Item must be a StorageItem"
        assert isinstance(remote, str), "Remote must be string"
        self._item = item
        self._remote = remote
        self._cli = cli
        self._hash_worker: Optional[HashWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Construct the dialog layout and metadata fields."""
        assert self._item is not None, "Item must be present"
        self.setWindowTitle(f"Properties - {self._item.name}")
        self.resize(500, 320)
        self.setWindowIcon(OutlineIcons.get_icon("info"))

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(8)

        self._add_field(form, "Name:", self._item.name)
        self._add_field(form, "Path:", self._item.path)
        self._add_field(form, "Size:", f"{format_bytes(self._item.size)} ({self._item.size:,} bytes)")
        self._add_field(form, "Type:", self._item.mime_type or ("Directory" if self._item.is_dir else "Object"))
        self._add_field(form, "Modified:", self._item.mod_time or "N/A")

        self._hash_edit = QLineEdit("Click Calculate...")
        self._hash_edit.setReadOnly(True)
        hash_btn = QPushButton("Calculate MD5")
        hash_btn.setIcon(OutlineIcons.get_icon("refresh"))
        hash_btn.clicked.connect(self._calculate_hash)

        hash_box = QHBoxLayout()
        hash_box.addWidget(self._hash_edit)
        hash_box.addWidget(hash_btn)
        form.addRow("MD5 Hash:", hash_box)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn:
            close_btn.setIcon(OutlineIcons.get_icon("cross"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def _add_field(self, form: QFormLayout, label: str, value: str) -> None:
        """Helper to append a readonly text row."""
        assert form is not None, "Form cannot be None"
        assert isinstance(label, str), "Label must be string"
        edit = QLineEdit(value)
        edit.setReadOnly(True)
        form.addRow(label, edit)

    def _calculate_hash(self) -> None:
        """Trigger async MD5 calculation."""
        assert self._cli is not None, "CLI executor required"
        self._hash_edit.setText("Computing checksum...")
        self._hash_worker = HashWorker(self._cli, self._remote, self._item.path, "md5")
        self._hash_worker.hash_ready.connect(self._on_hash_computed)
        self._hash_worker.start()

    def _on_hash_computed(self, hash_str: str) -> None:
        """Update hash line edit upon calculation completion."""
        assert isinstance(hash_str, str), "Hash string must be string"
        self._hash_edit.setText(hash_str)
