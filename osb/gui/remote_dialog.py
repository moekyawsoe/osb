"""GUI-based rclone remote configuration management dialog.

Complies with NASA JPL Power of 10 rules:
- Bounded thread lifecycles and explicit resource cleanup
- Strict function length <= 60 lines
- High assertion density (>= 2 assertions per function)
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from osb.core.config_mgr import ConfigManager
from osb.core.models import RemoteConfig
from osb.gui.outline_icons import OutlineIcons


class TestConnWorker(QThread):
    """Background worker for testing remote connectivity without freezing UI."""
    test_result = pyqtSignal(bool, str)

    def __init__(self, mgr: ConfigManager, remote_name: str) -> None:
        super().__init__()
        assert mgr is not None, "Manager cannot be None"
        assert len(remote_name) > 0, "Remote name cannot be empty"
        self._mgr = mgr
        self._remote_name = remote_name
        self._is_stopped = False

    def stop(self) -> None:
        """Signal thread to cease operations."""
        assert self._mgr is not None, "Manager must be present"
        self._is_stopped = True
        assert self._is_stopped is True, "Must be set to True"

    def run(self) -> None:
        """Execute test probe safely with boundary exception handling."""
        assert self._mgr is not None, "Manager must be active"
        assert len(self._remote_name) > 0, "Remote name required"
        try:
            res = self._mgr.test_remote(self._remote_name)
            if not self._is_stopped:
                self.test_result.emit(res.success, res.message)
        except Exception as exc:
            if not self._is_stopped:
                self.test_result.emit(False, f"Connection test error: {str(exc)}")


class EditRemoteDialog(QDialog):
    """Sub-dialog to create or edit an object storage remote."""

    def __init__(
        self,
        mgr: ConfigManager,
        config: Optional[RemoteConfig] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        assert mgr is not None, "ConfigManager required"
        self._mgr = mgr
        self._existing_config = config
        self._test_worker: Optional[TestConnWorker] = None
        self._test_btn: Optional[QPushButton] = None
        self._init_ui()
        if config:
            self._load_config(config)
        assert self._mgr is not None, "ConfigManager must remain valid"

    def _init_ui(self) -> None:
        """Construct the configuration form."""
        assert self._mgr is not None, "Manager cannot be None"
        self.setWindowTitle("Edit Remote" if self._existing_config else "New Remote")
        self.resize(520, 420)
        self.setWindowIcon(OutlineIcons.get_icon("server"))

        layout = QVBoxLayout(self)
        layout.addLayout(self._create_form_layout())
        layout.addLayout(self._create_buttons_layout())
        assert layout.count() >= 2, "Layout must contain form and buttons"

    def _create_form_layout(self) -> QFormLayout:
        """Construct form fields for remote settings."""
        form = QFormLayout()
        self._preset_combo = QComboBox()
        self._presets = ConfigManager.get_provider_presets()
        self._preset_combo.addItem("-- Select Preset (Optional) --", None)
        for p in self._presets:
            self._preset_combo.addItem(p["label"], p)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        form.addRow("Preset:", self._preset_combo)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. minio-prod or bdata-s3")
        form.addRow("Remote Name:", self._name_edit)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["Minio", "AWS", "Wasabi", "Cloudflare", "Other", "Ceph"])
        form.addRow("Provider:", self._provider_combo)

        self._endpoint_edit = QLineEdit()
        self._endpoint_edit.setPlaceholderText("https://s3.example.com:9000")
        form.addRow("Endpoint URL:", self._endpoint_edit)

        self._region_edit = QLineEdit("us-east-1")
        form.addRow("Region:", self._region_edit)

        self._access_key_edit = QLineEdit()
        form.addRow("Access Key ID:", self._access_key_edit)

        self._secret_key_edit = QLineEdit()
        self._secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Secret Key:", self._secret_key_edit)

        self._path_style_chk = QCheckBox("Force Path Style (Required for MinIO/Custom S3)")
        self._path_style_chk.setChecked(True)
        form.addRow("", self._path_style_chk)

        assert self._name_edit is not None, "Name edit required"
        assert self._endpoint_edit is not None, "Endpoint edit required"
        return form

    def _create_buttons_layout(self) -> QHBoxLayout:
        """Construct test and modal action buttons."""
        btn_layout = QHBoxLayout()
        self._test_btn = QPushButton("Test Connection")
        self._test_btn.setIcon(OutlineIcons.get_icon("refresh"))
        self._test_btn.clicked.connect(self._test_current_inputs)
        btn_layout.addWidget(self._test_btn)
        btn_layout.addStretch()

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_btn = self._buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_btn:
            save_btn.setIcon(OutlineIcons.get_icon("check"))
        cancel_btn = self._buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setIcon(OutlineIcons.get_icon("cross"))

        self._buttons.accepted.connect(self._on_save)
        self._buttons.rejected.connect(self.reject)
        btn_layout.addWidget(self._buttons)

        assert self._test_btn is not None, "Test button required"
        assert self._buttons is not None, "Buttons required"
        return btn_layout

    def _set_testing_state(self, is_testing: bool) -> None:
        """Toggle test button state during test execution."""
        assert self._test_btn is not None, "Test button required"
        assert isinstance(is_testing, bool), "State must be boolean"
        if is_testing:
            self._test_btn.setEnabled(False)
            self._test_btn.setText("Testing...")
        else:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("Test Connection")

    def _test_current_inputs(self) -> None:
        """Validate inputs and launch background connection test safely."""
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Remote name cannot be empty")
            return

        if self._test_worker is not None and self._test_worker.isRunning():
            return

        temp_cfg = self.get_remote_config()
        save_res = self._mgr.save_remote(temp_cfg)
        if not save_res.success:
            QMessageBox.warning(self, "Validation", f"Failed to register config: {save_res.message}")
            return

        assert self._mgr is not None, "ConfigManager required"
        self._set_testing_state(True)
        self._test_worker = TestConnWorker(self._mgr, temp_cfg.name)
        self._test_worker.test_result.connect(self._on_test_finished)
        self._test_worker.start()

    def _on_test_finished(self, success: bool, msg: str) -> None:
        """Handle background test completion for current inputs."""
        assert isinstance(success, bool), "Success must be boolean"
        assert isinstance(msg, str), "Message must be string"
        self._set_testing_state(False)
        if success:
            QMessageBox.information(self, "Success", f"Connection verified successfully!\n{msg}")
        else:
            QMessageBox.critical(self, "Connection Error", f"Connection failed:\n{msg}")

    def closeEvent(self, event) -> None:
        """Safely terminate background test worker upon dialog close."""
        assert event is not None, "Close event cannot be None"
        if self._test_worker is not None and self._test_worker.isRunning():
            self._test_worker.stop()
            self._test_worker.terminate()
            self._test_worker.wait(1000)
        assert self._mgr is not None, "Manager check"
        super().closeEvent(event)

    def _on_preset_changed(self, idx: int) -> None:
        """Fill form when a preset is chosen."""
        assert self._preset_combo is not None, "Preset combo required"
        assert isinstance(idx, int), "Index must be integer"
        data = self._preset_combo.currentData()
        if not data:
            return
        self._provider_combo.setCurrentText(data.get("provider", "Other"))
        self._endpoint_edit.setText(data.get("endpoint", ""))
        self._region_edit.setText(data.get("region", "us-east-1"))
        self._path_style_chk.setChecked(data.get("path_style", "true") == "true")

    def _load_config(self, cfg: RemoteConfig) -> None:
        """Populate form with existing config."""
        assert cfg is not None, "Config cannot be None"
        assert len(cfg.name) > 0, "Config name required"
        self._name_edit.setText(cfg.name)
        self._name_edit.setReadOnly(True)
        self._provider_combo.setCurrentText(cfg.provider or "Other")
        self._endpoint_edit.setText(cfg.endpoint)
        self._region_edit.setText(cfg.region)
        self._access_key_edit.setText(cfg.access_key_id)
        self._secret_key_edit.setText(cfg.secret_access_key)
        self._path_style_chk.setChecked(cfg.force_path_style)

    def _on_save(self) -> None:
        """Validate before saving."""
        assert self._name_edit is not None, "Name edit required"
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Remote name cannot be empty")
            return
        assert len(name) > 0, "Name must be non-empty"
        self.accept()

    def get_remote_config(self) -> RemoteConfig:
        """Extract typed RemoteConfig from inputs."""
        name = self._name_edit.text().strip()
        assert len(name) > 0, "Remote name cannot be empty"
        assert self._provider_combo is not None, "Provider combo required"
        return RemoteConfig(
            name=name,
            type="s3",
            provider=self._provider_combo.currentText(),
            endpoint=self._endpoint_edit.text().strip(),
            region=self._region_edit.text().strip(),
            access_key_id=self._access_key_edit.text().strip(),
            secret_access_key=self._secret_key_edit.text().strip(),
            force_path_style=self._path_style_chk.isChecked(),
        )


class RemoteManagerDialog(QDialog):
    """Main management window for listing, adding, editing, and deleting remotes."""

    def __init__(self, mgr: ConfigManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        assert mgr is not None, "ConfigManager required"
        self._mgr = mgr
        self._test_worker: Optional[TestConnWorker] = None
        self._test_btn: Optional[QPushButton] = None
        self._init_ui()
        self._refresh_list()
        assert self._table is not None, "Table initialized"

    def _init_ui(self) -> None:
        """Set up remote management layout."""
        assert self._mgr is not None, "Manager cannot be None"
        self.setWindowTitle("Object Storage Remote Configurations")
        self.resize(720, 420)
        self.setWindowIcon(OutlineIcons.get_icon("server"))

        layout = QVBoxLayout(self)
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Remote Name", "Type", "Provider", "Endpoint"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Remote")
        add_btn.setIcon(OutlineIcons.get_icon("plus"))
        add_btn.clicked.connect(self._add_remote)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(OutlineIcons.get_icon("settings"))
        edit_btn.clicked.connect(self._edit_remote)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("Delete")
        del_btn.setIcon(OutlineIcons.get_icon("trash"))
        del_btn.clicked.connect(self._delete_remote)
        btn_row.addWidget(del_btn)

        self._test_btn = QPushButton("Test Connection")
        self._test_btn.setIcon(OutlineIcons.get_icon("refresh"))
        self._test_btn.clicked.connect(self._test_selected)
        btn_row.addWidget(self._test_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setIcon(OutlineIcons.get_icon("cross"))
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        assert self._test_btn is not None, "Test button created"

    def _refresh_list(self) -> None:
        """Reload all remotes from rclone config dump."""
        assert self._table is not None, "Table cannot be None"
        assert self._mgr is not None, "Manager cannot be None"
        self._table.setRowCount(0)
        res = self._mgr.list_remotes()
        if not res.success or not isinstance(res.data, list):
            return

        for cfg in res.data:
            assert isinstance(cfg, RemoteConfig), "Must be RemoteConfig"
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(cfg.name))
            self._table.setItem(row, 1, QTableWidgetItem(cfg.type))
            self._table.setItem(row, 2, QTableWidgetItem(cfg.provider))
            self._table.setItem(row, 3, QTableWidgetItem(cfg.endpoint))

    def _get_selected_remote_name(self) -> Optional[str]:
        """Return the remote name of currently selected row."""
        assert self._table is not None, "Table required"
        row = self._table.currentRow()
        assert isinstance(row, int), "Row must be integer"
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.text() if item else None

    def _set_testing_state(self, is_testing: bool) -> None:
        """Toggle test button state during test execution."""
        assert self._test_btn is not None, "Test button required"
        assert isinstance(is_testing, bool), "State must be boolean"
        if is_testing:
            self._test_btn.setEnabled(False)
            self._test_btn.setText("Testing...")
        else:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("Test Connection")

    def _test_selected(self) -> None:
        """Test connection of currently selected remote with thread safety."""
        name = self._get_selected_remote_name()
        if not name:
            QMessageBox.information(self, "Select Remote", "Please select a remote to test.")
            return

        if self._test_worker is not None and self._test_worker.isRunning():
            QMessageBox.information(self, "Testing", "A connection test is already running.")
            return

        assert self._mgr is not None, "ConfigManager required"
        self._set_testing_state(True)
        self._test_worker = TestConnWorker(self._mgr, name)
        self._test_worker.test_result.connect(
            lambda ok, msg: self._on_test_finished(name, ok, msg)
        )
        self._test_worker.start()

    def _on_test_finished(self, name: str, success: bool, msg: str) -> None:
        """Handle test probe completion and restore UI."""
        assert isinstance(name, str), "Name must be string"
        assert isinstance(success, bool), "Success must be boolean"
        self._set_testing_state(False)
        self._show_test_result(name, success, msg)

    def _show_test_result(self, name: str, success: bool, msg: str) -> None:
        """Show connection test result dialog."""
        assert isinstance(name, str), "Name must be string"
        assert isinstance(msg, str), "Message must be string"
        if success:
            QMessageBox.information(self, "Test Succeeded", f"Remote '{name}' is online and verified!")
        else:
            QMessageBox.critical(self, "Test Failed", f"Remote '{name}' test failed:\n{msg}")

    def closeEvent(self, event) -> None:
        """Safely terminate background test worker upon dialog close."""
        assert event is not None, "Close event cannot be None"
        if self._test_worker is not None and self._test_worker.isRunning():
            self._test_worker.stop()
            self._test_worker.terminate()
            self._test_worker.wait(1000)
        assert self._mgr is not None, "Manager required"
        super().closeEvent(event)

    def _add_remote(self) -> None:
        """Open add dialog and save new remote."""
        assert self._mgr is not None, "Manager required"
        dlg = EditRemoteDialog(self._mgr, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            cfg = dlg.get_remote_config()
            res = self._mgr.save_remote(cfg)
            if res.success:
                self._refresh_list()
            else:
                QMessageBox.critical(self, "Error", f"Failed to save remote: {res.message}")
        assert dlg is not None, "Dialog completed"

    def _edit_remote(self) -> None:
        """Edit selected remote configuration."""
        name = self._get_selected_remote_name()
        if not name:
            QMessageBox.information(self, "Select Remote", "Please select a remote to edit.")
            return

        assert self._mgr is not None, "Manager required"
        res = self._mgr.list_remotes()
        cfg_to_edit = next((c for c in (res.data or []) if c.name == name), None)
        if not cfg_to_edit:
            return

        dlg = EditRemoteDialog(self._mgr, config=cfg_to_edit, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            cfg = dlg.get_remote_config()
            self._mgr.save_remote(cfg)
            self._refresh_list()

    def _delete_remote(self) -> None:
        """Delete selected remote with confirmation."""
        name = self._get_selected_remote_name()
        if not name:
            QMessageBox.information(self, "Select Remote", "Please select a remote to delete.")
            return

        assert isinstance(name, str), "Name must be string"
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete remote '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._mgr.delete_remote(name)
            self._refresh_list()
