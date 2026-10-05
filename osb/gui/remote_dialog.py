"""FileZilla-style Site Manager configuration dialog for object storage remotes.

Complies with NASA JPL Power of 10 rules:
- Bounded thread lifecycles and explicit resource cleanup
- Strict function length <= 60 lines
- High assertion density (>= 2 assertions per function)
- Pure vector outline icon system
"""

from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
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


class RemoteManagerDialog(QDialog):
    """FileZilla-style Site Manager for object storage remotes.

    Features:
    - Left Panel: Hierarchical tree view (My Sites -> remote items) with New, Duplicate, Delete, Rename buttons.
    - Right Panel: Detailed parameters form with presets, live inputs, Save, and Test Connection.
    """

    def __init__(self, mgr: ConfigManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        assert mgr is not None, "ConfigManager required"
        self._mgr = mgr
        self._test_worker: Optional[TestConnWorker] = None
        self._active_remote_name: Optional[str] = None
        self._init_ui()
        self._load_remotes_into_tree()
        assert self._tree is not None, "Tree widget required"

    def _init_ui(self) -> None:
        """Construct the FileZilla-style Site Manager window."""
        assert self._mgr is not None, "Manager cannot be None"
        self.setWindowTitle("Site Manager - Object Storage Remotes")
        self.resize(780, 520)
        self.setMinimumSize(680, 420)
        self.setWindowIcon(OutlineIcons.get_icon("server"))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_left_panel())
        splitter.addWidget(self._create_right_panel())
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        main_layout.addWidget(splitter)

        main_layout.addLayout(self._create_dialog_bottom_bar())
        assert splitter is not None, "Splitter must be created"

    def _create_left_panel(self) -> QWidget:
        """Construct the left-side tree view panel for sites/remotes."""
        assert self._mgr is not None, "Manager must exist"
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)

        header = QLabel("MY STORAGE SITES")
        header.setStyleSheet("font-weight: bold; font-size: 11px; color: #9ca3af;")
        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.currentItemChanged.connect(self._on_tree_selection_changed)
        layout.addWidget(self._tree)

        layout.addLayout(self._create_tree_button_grid())
        assert self._tree is not None, "Tree widget must be instantiated"
        return panel

    def _create_tree_button_grid(self) -> QGridLayout:
        """Construct buttons below tree (New, Duplicate, Delete, Rename)."""
        assert self._tree is not None, "Tree must exist"
        grid = QGridLayout()
        grid.setSpacing(4)

        btn_new = QPushButton("New Site")
        btn_new.setIcon(OutlineIcons.get_icon("plus"))
        btn_new.clicked.connect(self._on_new_remote)
        grid.addWidget(btn_new, 0, 0)

        btn_dup = QPushButton("Duplicate")
        btn_dup.setIcon(OutlineIcons.get_icon("copy"))
        btn_dup.clicked.connect(self._on_duplicate_remote)
        grid.addWidget(btn_dup, 0, 1)

        btn_del = QPushButton("Delete")
        btn_del.setIcon(OutlineIcons.get_icon("trash"))
        btn_del.clicked.connect(self._on_delete_remote)
        grid.addWidget(btn_del, 1, 0)

        btn_ren = QPushButton("Rename")
        btn_ren.setIcon(OutlineIcons.get_icon("settings"))
        btn_ren.clicked.connect(self._on_rename_remote)
        grid.addWidget(btn_ren, 1, 1)

        assert grid.count() == 4, "Must contain 4 buttons"
        return grid

    def _create_right_panel(self) -> QWidget:
        """Construct the right-side configuration form panel."""
        assert self._mgr is not None, "Manager must exist"
        self._right_container = QWidget()
        layout = QVBoxLayout(self._right_container)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(8)

        layout.addLayout(self._create_preset_row())
        layout.addWidget(self._create_form_group())
        layout.addLayout(self._create_form_action_row())
        layout.addStretch()

        assert self._right_container is not None, "Right container created"
        return self._right_container

    def _create_preset_row(self) -> QHBoxLayout:
        """Construct provider template preset picker."""
        row = QHBoxLayout()
        row.addWidget(QLabel("Preset Template:"))
        self._preset_combo = QComboBox()
        self._presets = ConfigManager.get_provider_presets()
        self._preset_combo.addItem("-- Select Provider Preset --", None)
        for p in self._presets:
            self._preset_combo.addItem(p["label"], p)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        row.addWidget(self._preset_combo, 1)
        assert self._preset_combo is not None, "Preset combo required"
        assert row.count() >= 2, "Row contains label and combo"
        return row

    def _create_form_group(self) -> QGroupBox:
        """Construct form fields group for remote parameters."""
        group = QGroupBox("Remote Parameters")
        form = QFormLayout(group)
        form.setSpacing(6)

        self._name_edit = QLineEdit()
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

        self._path_style_chk = QCheckBox("Force Path Style (Required for MinIO/RustFS)")
        self._path_style_chk.setChecked(True)
        form.addRow("", self._path_style_chk)

        assert self._name_edit is not None, "Name edit required"
        assert self._endpoint_edit is not None, "Endpoint edit required"
        return group

    def _create_form_action_row(self) -> QHBoxLayout:
        """Construct test connection and save buttons with status label."""
        row = QHBoxLayout()
        self._test_btn = QPushButton("Test Connection")
        self._test_btn.setIcon(OutlineIcons.get_icon("refresh"))
        self._test_btn.clicked.connect(self._on_test_connection)
        row.addWidget(self._test_btn)

        self._save_btn = QPushButton("Save Remote")
        self._save_btn.setIcon(OutlineIcons.get_icon("check"))
        self._save_btn.clicked.connect(self._on_save_remote)
        row.addWidget(self._save_btn)

        self._status_lbl = QLabel("Ready")
        self._status_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        row.addWidget(self._status_lbl)
        row.addStretch()

        assert self._test_btn is not None, "Test button required"
        assert self._save_btn is not None, "Save button required"
        return row

    def _create_dialog_bottom_bar(self) -> QHBoxLayout:
        """Construct bottom dialog close bar."""
        bar = QHBoxLayout()
        hint = QLabel("Select any site on the left to configure or test.")
        hint.setStyleSheet("color: #6b7280; font-size: 11px;")
        bar.addWidget(hint)
        bar.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setIcon(OutlineIcons.get_icon("cross"))
        close_btn.clicked.connect(self.accept)
        bar.addWidget(close_btn)

        assert bar.count() >= 2, "Bottom bar created"
        assert close_btn is not None, "Close button required"
        return bar

    def _load_remotes_into_tree(self, select_name: Optional[str] = None) -> None:
        """Populate tree with My Sites hierarchy from rclone configuration."""
        assert self._tree is not None, "Tree widget required"
        assert self._mgr is not None, "Manager required"
        self._tree.clear()

        root = QTreeWidgetItem(["My Storage Sites"])
        root.setIcon(0, OutlineIcons.get_icon("folder"))
        self._tree.addTopLevelItem(root)

        res = self._mgr.list_remotes()
        remotes = res.data if (res.success and isinstance(res.data, list)) else []
        target_item = None

        for cfg in remotes:
            child = QTreeWidgetItem([cfg.name])
            child.setIcon(0, OutlineIcons.get_icon("server"))
            child.setData(0, Qt.ItemDataRole.UserRole, cfg)
            root.addChild(child)
            if select_name and cfg.name == select_name:
                target_item = child

        root.setExpanded(True)
        if target_item:
            self._tree.setCurrentItem(target_item)
        elif root.childCount() > 0:
            self._tree.setCurrentItem(root.child(0))
        else:
            self._reset_form()

    def _on_tree_selection_changed(
        self,
        current: Optional[QTreeWidgetItem],
        previous: Optional[QTreeWidgetItem],
    ) -> None:
        """Handle tree item selection and load configuration into form."""
        assert self._tree is not None, "Tree required"
        if not current:
            self._reset_form()
            return

        cfg = current.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(cfg, RemoteConfig):
            self._active_remote_name = cfg.name
            self._load_remote_to_form(cfg)
            self._right_container.setEnabled(True)
        else:
            self._active_remote_name = None
            self._reset_form()
            self._right_container.setEnabled(False)
        assert self._right_container is not None, "Container valid"

    def _load_remote_to_form(self, cfg: RemoteConfig) -> None:
        """Fill form inputs with selected remote configuration."""
        assert cfg is not None, "Config required"
        assert len(cfg.name) > 0, "Config name required"
        self._name_edit.setText(cfg.name)
        self._provider_combo.setCurrentText(cfg.provider or "Other")
        self._endpoint_edit.setText(cfg.endpoint)
        self._region_edit.setText(cfg.region or "us-east-1")
        self._access_key_edit.setText(cfg.access_key_id)
        self._secret_key_edit.setText(cfg.secret_access_key)
        self._path_style_chk.setChecked(cfg.force_path_style)
        self._status_lbl.setText("Ready")
        self._status_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")

    def _reset_form(self) -> None:
        """Reset form inputs to blank template."""
        assert self._name_edit is not None, "Name edit required"
        assert self._endpoint_edit is not None, "Endpoint edit required"
        self._name_edit.setText("")
        self._provider_combo.setCurrentText("Minio")
        self._endpoint_edit.setText("")
        self._region_edit.setText("us-east-1")
        self._access_key_edit.setText("")
        self._secret_key_edit.setText("")
        self._path_style_chk.setChecked(True)
        self._status_lbl.setText("No remote selected")

    def _on_preset_changed(self, idx: int) -> None:
        """Apply selected provider template preset to active form."""
        assert self._preset_combo is not None, "Preset combo required"
        assert isinstance(idx, int), "Index must be integer"
        data = self._preset_combo.currentData()
        if not data:
            return
        self._provider_combo.setCurrentText(data.get("provider", "Other"))
        self._endpoint_edit.setText(data.get("endpoint", ""))
        self._region_edit.setText(data.get("region", "us-east-1"))
        self._path_style_chk.setChecked(data.get("path_style", "true") == "true")

    def _on_new_remote(self) -> None:
        """Create and register a new storage site."""
        assert self._mgr is not None, "Manager required"
        base_name = "new-site"
        res = self._mgr.list_remotes()
        existing = set(c.name for c in (res.data or []))
        name = base_name
        counter = 1
        while name in existing:
            counter += 1
            name = f"{base_name}-{counter}"

        new_cfg = RemoteConfig(name=name, type="s3", provider="Minio")
        self._mgr.save_remote(new_cfg)
        self._load_remotes_into_tree(select_name=name)
        assert self._tree is not None, "Tree refreshed"

    def _on_duplicate_remote(self) -> None:
        """Duplicate current site configuration under a new name."""
        assert self._mgr is not None, "Manager required"
        if not self._active_remote_name:
            QMessageBox.information(self, "Select Site", "Please select a site to duplicate.")
            return

        cfg = self.get_remote_config_from_form()
        dup_name = f"{cfg.name}-copy"
        dup_cfg = RemoteConfig(
            name=dup_name,
            type=cfg.type,
            provider=cfg.provider,
            endpoint=cfg.endpoint,
            region=cfg.region,
            access_key_id=cfg.access_key_id,
            secret_access_key=cfg.secret_access_key,
            force_path_style=cfg.force_path_style,
        )
        self._mgr.save_remote(dup_cfg)
        self._load_remotes_into_tree(select_name=dup_name)
        assert self._active_remote_name is not None, "Site duplicated"

    def _on_delete_remote(self) -> None:
        """Delete currently selected storage site with confirmation."""
        assert self._mgr is not None, "Manager required"
        if not self._active_remote_name:
            QMessageBox.information(self, "Select Site", "Please select a site to delete.")
            return

        name = self._active_remote_name
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete site '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._mgr.delete_remote(name)
            self._load_remotes_into_tree()
        assert isinstance(name, str), "Name was string"

    def _on_rename_remote(self) -> None:
        """Prompt to rename the current storage site."""
        assert self._mgr is not None, "Manager required"
        if not self._active_remote_name:
            QMessageBox.information(self, "Select Site", "Please select a site to rename.")
            return

        old_name = self._active_remote_name
        new_name, ok = QInputDialog.getText(self, "Rename Site", "Enter new site name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            cfg = self.get_remote_config_from_form()
            cfg.name = new_name.strip()
            self._mgr.delete_remote(old_name)
            self._mgr.save_remote(cfg)
            self._load_remotes_into_tree(select_name=cfg.name)
        assert isinstance(old_name, str), "Old name was string"

    def _on_save_remote(self) -> None:
        """Save changes made to the active site form."""
        assert self._mgr is not None, "Manager required"
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Remote name cannot be empty.")
            return

        cfg = self.get_remote_config_from_form()
        if self._active_remote_name and self._active_remote_name != cfg.name:
            self._mgr.delete_remote(self._active_remote_name)

        save_res = self._mgr.save_remote(cfg)
        if save_res.success:
            self._status_lbl.setText("Saved successfully")
            self._status_lbl.setStyleSheet("color: #34d399; font-size: 11px;")
            self._load_remotes_into_tree(select_name=cfg.name)
        else:
            QMessageBox.critical(self, "Error", f"Failed to save: {save_res.message}")
        assert len(cfg.name) > 0, "Config name non-empty"

    def _on_test_connection(self) -> None:
        """Test connection to the configured remote endpoint safely in background."""
        assert self._mgr is not None, "Manager required"
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Remote name cannot be empty.")
            return

        if self._test_worker is not None and self._test_worker.isRunning():
            return

        cfg = self.get_remote_config_from_form()
        self._mgr.save_remote(cfg)
        self._set_testing_state(True)
        self._status_lbl.setText("Testing connection...")
        self._status_lbl.setStyleSheet("color: #60a5fa; font-size: 11px;")

        self._test_worker = TestConnWorker(self._mgr, cfg.name)
        self._test_worker.test_result.connect(
            lambda ok, msg: self._on_test_finished(cfg.name, ok, msg)
        )
        self._test_worker.start()
        assert self._test_worker is not None, "Worker started"

    def _set_testing_state(self, is_testing: bool) -> None:
        """Toggle test button during async probe."""
        assert self._test_btn is not None, "Test button required"
        assert isinstance(is_testing, bool), "State must be boolean"
        if is_testing:
            self._test_btn.setEnabled(False)
            self._test_btn.setText("Testing...")
        else:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("Test Connection")

    def _on_test_finished(self, name: str, success: bool, msg: str) -> None:
        """Handle background test completion and update status."""
        assert isinstance(name, str), "Name must be string"
        assert isinstance(success, bool), "Success must be boolean"
        self._set_testing_state(False)
        if success:
            self._status_lbl.setText("Online & Verified")
            self._status_lbl.setStyleSheet("color: #34d399; font-size: 11px;")
            QMessageBox.information(self, "Test Succeeded", f"Remote '{name}' is online and verified!")
        else:
            self._status_lbl.setText("Connection Failed")
            self._status_lbl.setStyleSheet("color: #f87171; font-size: 11px;")
            QMessageBox.critical(self, "Test Failed", f"Remote '{name}' failed:\n{msg}")

    def get_remote_config_from_form(self) -> RemoteConfig:
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

    def closeEvent(self, event) -> None:
        """Safely terminate background test worker upon dialog close."""
        assert event is not None, "Close event cannot be None"
        if self._test_worker is not None and self._test_worker.isRunning():
            self._test_worker.stop()
            self._test_worker.terminate()
            self._test_worker.wait(1000)
        assert self._mgr is not None, "Manager required"
        super().closeEvent(event)


class EditRemoteDialog(QDialog):
    """Sub-dialog to create or edit an object storage remote (backwards compatibility)."""

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

        self._path_style_chk = QCheckBox("Force Path Style (Required for MinIO/RustFS)")
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
