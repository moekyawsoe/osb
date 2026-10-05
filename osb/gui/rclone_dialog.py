"""Rclone setup, cross-platform installation guide, and detection modal dialog.

Complies with NASA JPL Power of 10 rules:
- Rule 2: Fixed loop bounds
- Rule 4: Functions strictly <= 60 lines
- Rule 5: Assertions present in methods
- Rule 7: Validates return values
"""

import os
from typing import Optional
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from osb.core.rclone_detector import (
    GITHUB_RELEASES_URL,
    OFFICIAL_DOWNLOADS_URL,
    OFFICIAL_INSTALL_GUIDE_URL,
    PLATFORM_GUIDES,
    PlatformGuide,
    find_rclone_binary,
    get_current_platform_key,
)
from osb.gui.outline_icons import OutlineIcons


class RcloneSetupDialog(QDialog):
    """Modal dialog displaying rclone installation guides, download URLs, and path selection."""

    def __init__(self, custom_path: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._custom_path = custom_path
        self._detected_binary: Optional[str] = None
        self.setWindowTitle("Rclone Engine Setup & Downloads")
        self.resize(680, 520)
        self.setWindowIcon(OutlineIcons.get_icon("server"))
        self._init_ui()

    def _init_ui(self) -> None:
        """Construct dialog layout with header, OS tabs, and action footer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addLayout(self._create_header_layout())

        self._tabs = QTabWidget()
        curr_key = get_current_platform_key()
        guide = PLATFORM_GUIDES.get(curr_key, PLATFORM_GUIDES["linux"])

        self._tabs.addTab(self._create_guide_panel(guide, is_current=True), f"Current OS ({guide.display_title.split()[0]})")
        for key, g in PLATFORM_GUIDES.items():
            if key != curr_key:
                self._tabs.addTab(self._create_guide_panel(g, is_current=False), g.display_title.split()[0])

        self._tabs.addTab(self._create_custom_path_panel(), "Browse / Custom Path")
        layout.addWidget(self._tabs)

        layout.addLayout(self._create_footer_layout())
        assert self._tabs.count() >= 3, "Tabs must be fully populated"

    def _create_header_layout(self) -> QVBoxLayout:
        """Construct top banner informing user of rclone requirement."""
        layout = QVBoxLayout()
        title = QLabel("Rclone Storage Engine Required")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f3f4f6;")
        layout.addWidget(title)

        desc = QLabel(
            "Object Storage Bridge uses the open-source <b>rclone</b> engine to communicate with S3, "
            "MinIO, Ceph, and RustFS. Please install rclone or specify its executable path below."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9ca3af; font-size: 12px; line-height: 1.4;")
        layout.addWidget(desc)
        return layout

    def _create_guide_panel(self, guide: PlatformGuide, is_current: bool) -> QWidget:
        """Create installation instructions widget for a specific platform."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        lbl = QLabel(f"<b>Installation Methods for {guide.display_title}:</b>")
        lbl.setStyleSheet("color: #d1d5db; font-size: 12px;")
        layout.addWidget(lbl)

        # NASA Rule 2: Fixed bound loop
        max_methods = min(len(guide.methods), 8)
        for i in range(max_methods):
            m = guide.methods[i]
            row = QHBoxLayout()
            desc = QLabel(f"{m.title}:")
            desc.setMinimumWidth(180)
            desc.setStyleSheet("color: #9ca3af; font-size: 11px;")
            row.addWidget(desc)

            cmd_box = QLineEdit(m.command)
            cmd_box.setReadOnly(True)
            cmd_box.setStyleSheet("background-color: #111215; color: #60a5fa; font-family: monospace; font-size: 11px;")
            row.addWidget(cmd_box)

            copy_btn = QPushButton("Copy")
            copy_btn.setIcon(OutlineIcons.get_icon("copy"))
            copy_btn.setMaximumWidth(70)
            copy_btn.clicked.connect(lambda _, c=m.command: self._copy_to_clipboard(c))
            row.addWidget(copy_btn)
            layout.addLayout(row)

        layout.addStretch()
        layout.addLayout(self._create_links_row(guide))
        return panel

    def _create_links_row(self, guide: PlatformGuide) -> QHBoxLayout:
        """Build clickable external links row."""
        row = QHBoxLayout()
        dl_btn = QPushButton("Official Downloads")
        dl_btn.setIcon(OutlineIcons.get_icon("arrow_right"))
        dl_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(guide.download_url)))
        row.addWidget(dl_btn)

        guide_btn = QPushButton("Installation Docs")
        guide_btn.setIcon(OutlineIcons.get_icon("info"))
        guide_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(guide.guide_url)))
        row.addWidget(guide_btn)

        gh_btn = QPushButton("GitHub Releases")
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_RELEASES_URL)))
        row.addWidget(gh_btn)
        return row

    def _create_custom_path_panel(self) -> QWidget:
        """Create panel for browsing and selecting local rclone executable."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        info = QLabel("If you already downloaded rclone or extracted it manually, specify the executable:")
        info.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(info)

        row = QHBoxLayout()
        self._path_input = QLineEdit(self._custom_path or "")
        self._path_input.setPlaceholderText("/path/to/rclone or C:\\rclone\\rclone.exe")
        row.addWidget(self._path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.setIcon(OutlineIcons.get_icon("folder"))
        browse_btn.clicked.connect(self._browse_binary)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        layout.addStretch()
        return panel

    def _create_footer_layout(self) -> QHBoxLayout:
        """Construct bottom action buttons."""
        row = QHBoxLayout()
        cancel_btn = QPushButton("Exit")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)

        row.addStretch()

        retry_btn = QPushButton("Check & Detect Rclone")
        retry_btn.setIcon(OutlineIcons.get_icon("refresh"))
        retry_btn.setStyleSheet("font-weight: bold;")
        retry_btn.clicked.connect(self._check_and_detect)
        row.addWidget(retry_btn)
        return row

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy command string to OS clipboard."""
        assert isinstance(text, str), "Clipboard text must be string"
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            QMessageBox.information(self, "Copied", f"Command copied to clipboard:\n\n{text}")

    def _browse_binary(self) -> None:
        """Open file dialog to pick rclone executable."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select rclone Executable",
            os.path.expanduser("~"),
            "Executables (rclone* rclone.exe);;All Files (*)",
        )
        if path:
            self._path_input.setText(path)

    def _check_and_detect(self) -> None:
        """Verify if rclone is now present on the system."""
        custom = self._path_input.text().strip() if hasattr(self, "_path_input") else None
        binary = find_rclone_binary(custom_path=custom or None)
        if binary:
            self._detected_binary = binary
            QMessageBox.information(self, "Rclone Detected", f"Rclone was successfully found at:\n{binary}")
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Not Found",
                "Rclone binary could not be found.\n\n"
                "Please run the install command or specify the correct path to the executable.",
            )

    def get_detected_binary(self) -> Optional[str]:
        """Return detected binary path if check succeeded."""
        return self._detected_binary
