"""Bucket creation and storage statistics inspection dialogs.

Complies with NASA JPL Power of 10 rules.
"""

from typing import Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from osb.core.rclone_cli import RcloneCli
from osb.core.utils import format_bytes, is_valid_bucket_name
from osb.gui.outline_icons import OutlineIcons


class CreateBucketDialog(QDialog):
    """Dialog for creating a new S3-compliant bucket."""

    def __init__(self, remote_name: str, parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        assert isinstance(remote_name, str) and len(remote_name) > 0, "Remote name required"
        self._remote_name = remote_name
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        self.setWindowTitle(f"Create Bucket - {self._remote_name}")
        self.resize(420, 200)
        self.setWindowIcon(OutlineIcons.get_icon("bucket"))

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. my-app-backup-bucket")
        self._name_edit.textChanged.connect(self._validate_input)
        form.addRow("Bucket Name:", self._name_edit)

        self._region_combo = QComboBox()
        self._region_combo.addItems(["default", "us-east-1", "us-west-1", "us-west-2", "eu-central-1", "ap-southeast-1"])
        form.addRow("Region:", self._region_combo)

        self._status_label = QLabel("Enter a DNS-compliant lowercase bucket name.")
        self._status_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        form.addRow("", self._status_label)

        layout.addLayout(form)
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setIcon(OutlineIcons.get_icon("check"))
            ok_btn.setEnabled(False)
        cancel_btn = self._buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setIcon(OutlineIcons.get_icon("cross"))

        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)


    def _validate_input(self, text: str) -> None:
        """Validate bucket name on every keystroke."""
        assert self._status_label is not None, "Status label cannot be None"
        valid, msg = is_valid_bucket_name(text.strip())
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(valid)
        self._status_label.setText(msg)
        self._status_label.setStyleSheet("color: #9ca3af; font-size: 11px;" if valid else "color: #f87171; font-size: 11px;")

    def _on_accept(self) -> None:
        """Final check before accepting dialog."""
        valid, _ = is_valid_bucket_name(self.get_bucket_name())
        if valid:
            self.accept()

    def get_bucket_name(self) -> str:
        """Return sanitized bucket name."""
        name = self._name_edit.text().strip().lower()
        assert len(name) >= 3, "Bucket name must be at least 3 chars"
        return name


class BucketStatsWorker(QThread):
    """Worker to fetch bucket storage size and object count."""
    stats_ready = pyqtSignal(bool, dict, str)

    def __init__(self, cli: RcloneCli, remote: str, bucket: str) -> None:
        super().__init__()
        assert cli is not None, "CLI executor required"
        assert len(remote) > 0 and len(bucket) > 0, "Remote and bucket must be non-empty"
        self._cli = cli
        self._remote = remote
        self._bucket = bucket

    def run(self) -> None:
        """Execute rclone size and emit telemetry."""
        assert self._cli is not None, "CLI executor required"
        res = self._cli.get_size_stats(self._remote, self._bucket)
        if res.success and isinstance(res.data, dict):
            self.stats_ready.emit(True, res.data, "")
        else:
            self.stats_ready.emit(False, {}, res.message)


class BucketPropertiesDialog(QDialog):
    """Inspect bucket statistics (object count, total bytes)."""

    def __init__(self, remote: str, bucket: str, cli: RcloneCli, parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        assert len(remote) > 0 and len(bucket) > 0, "Remote and bucket required"
        self._remote = remote
        self._bucket = bucket
        self._cli = cli
        self._worker: Optional[BucketStatsWorker] = None
        self._init_ui()
        self._load_stats()

    def _init_ui(self) -> None:
        """Construct the properties dialog."""
        self.setWindowTitle(f"Bucket Properties - {self._bucket}")
        self.resize(440, 240)
        self.setWindowIcon(OutlineIcons.get_icon("bucket"))

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._add_field(form, "Storage Remote:", self._remote)
        self._add_field(form, "Bucket:", self._bucket)
        self._count_edit = self._add_field(form, "Total Objects:", "Calculating...")
        self._size_edit = self._add_field(form, "Total Size:", "Calculating...")

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn:
            close_btn.setIcon(OutlineIcons.get_icon("cross"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def _add_field(self, form: QFormLayout, label: str, val: str) -> QLineEdit:
        """Helper to append readonly field."""
        assert form is not None, "Form cannot be None"
        edit = QLineEdit(val)
        edit.setReadOnly(True)
        form.addRow(label, edit)
        return edit

    def _load_stats(self) -> None:
        """Start async size calculation worker."""
        assert self._cli is not None, "CLI executor required"
        self._worker = BucketStatsWorker(self._cli, self._remote, self._bucket)
        self._worker.stats_ready.connect(self._on_stats_ready)
        self._worker.start()

    def _on_stats_ready(self, success: bool, stats: dict, err: str) -> None:
        """Update display with fetched statistics."""
        assert self._count_edit is not None and self._size_edit is not None, "Fields cannot be None"
        if success:
            count = int(stats.get("count", 0))
            bytes_val = int(stats.get("bytes", 0))
            self._count_edit.setText(f"{count:,} objects")
            self._size_edit.setText(f"{format_bytes(bytes_val)} ({bytes_val:,} bytes)")
        else:
            self._count_edit.setText("Failed to calculate")
            self._size_edit.setText(err or "Error calculating size")
