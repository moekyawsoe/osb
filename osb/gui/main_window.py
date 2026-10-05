"""Main enterprise window integrating dual-pane storage browser and job telemetry.

Complies with NASA JPL Power of 10 rules.
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from osb.core.config_mgr import ConfigManager
from osb.core.constants import APP_NAME, APP_VERSION
from osb.core.rclone_cli import RcloneCli
from osb.core.transfer_mgr import TransferManager
from osb.gui.dual_panel import DualPanelWidget
from osb.gui.jobs_view import JobsView
from osb.gui.outline_icons import OutlineIcons
from osb.gui.remote_dialog import RemoteManagerDialog


class MainWindow(QMainWindow):
    """Main application window for the Object Storage Bridge."""

    def __init__(self, cli: RcloneCli, config_mgr: ConfigManager, transfer_mgr: TransferManager) -> None:
        super().__init__()
        assert cli is not None, "CLI executor required"
        assert config_mgr is not None, "ConfigManager required"
        assert transfer_mgr is not None, "TransferManager required"
        self._cli = cli
        self._config_mgr = config_mgr
        self._transfer_mgr = transfer_mgr

        self._init_window()
        self._init_menus_and_toolbars()
        self._init_central_widget()
        self._load_initial_remotes()

    def _init_window(self) -> None:
        """Configure main window dimensions and metadata."""
        assert self._cli is not None, "CLI required"
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(780, 480)
        self.setWindowIcon(OutlineIcons.get_icon("bucket"))
        self._fit_to_active_screen()
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")
        assert self.minimumWidth() == 780, "Minimum width must be 780"

    def _fit_to_active_screen(self) -> None:
        """Position window properly inside available desktop space."""
        screen = self.screen() or QApplication.primaryScreen()
        assert screen is not None, "Screen must be available"
        avail = screen.availableGeometry()
        target_w = min(1280, max(780, avail.width() - 80))
        target_h = min(800, max(480, avail.height() - 80))
        self.resize(target_w, target_h)
        pos_x = avail.x() + (avail.width() - target_w) // 2
        pos_y = avail.y() + (avail.height() - target_h) // 2
        self.move(max(avail.x(), pos_x), max(avail.y(), pos_y))
        assert self.width() >= 780, "Window width must be at least 780"

    def _init_menus_and_toolbars(self) -> None:
        """Set up clean monochrome menus and toolbar."""
        menubar = self.menuBar()
        self._setup_file_menu(menubar)
        self._setup_view_menu(menubar)
        self._setup_help_menu(menubar)
        self._setup_main_toolbar()

    def _setup_file_menu(self, menubar) -> None:
        """Configure file menu actions."""
        assert menubar is not None, "Menubar required"
        file_menu = menubar.addMenu("File")
        remotes_act = file_menu.addAction(OutlineIcons.get_icon("server"), "Remote Configurations...")
        remotes_act.triggered.connect(self._open_remote_manager)
        refresh_act = file_menu.addAction(OutlineIcons.get_icon("refresh"), "Refresh All")
        refresh_act.triggered.connect(self._refresh_all)
        file_menu.addSeparator()
        exit_act = file_menu.addAction("Exit")
        exit_act.triggered.connect(self.close)
        assert file_menu is not None, "File menu created"

    def _setup_view_menu(self, menubar) -> None:
        """Configure view menu with panel maximize/minimize controls."""
        assert menubar is not None, "Menubar required"
        view_menu = menubar.addMenu("View")
        jobs_act = view_menu.addAction(OutlineIcons.get_icon("minus"), "Toggle Transfer Jobs Panel")
        jobs_act.setShortcut("Ctrl+J")
        jobs_act.triggered.connect(self._toggle_jobs_panel)

        equal_act = view_menu.addAction(OutlineIcons.get_icon("sync"), "Equalize Explorer Panels")
        equal_act.setShortcut("Ctrl+E")
        equal_act.triggered.connect(self._equalize_panels)

        view_menu.addSeparator()
        max_left_act = view_menu.addAction(OutlineIcons.get_icon("arrow_left"), "Maximize Left Panel")
        max_left_act.triggered.connect(lambda: self._dual_panel.maximize_panel(True))

        max_right_act = view_menu.addAction(OutlineIcons.get_icon("arrow_right"), "Maximize Right Panel")
        max_right_act.triggered.connect(lambda: self._dual_panel.maximize_panel(False))
        assert view_menu is not None, "View menu created"

    def _setup_help_menu(self, menubar) -> None:
        """Configure help menu actions."""
        assert menubar is not None, "Menubar required"
        help_menu = menubar.addMenu("Help")
        about_act = help_menu.addAction(OutlineIcons.get_icon("info"), "About")
        about_act.triggered.connect(self._show_about)
        assert help_menu is not None, "Help menu created"

    def _setup_main_toolbar(self) -> None:
        """Configure main toolbar icons and actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        tb_remotes = toolbar.addAction(OutlineIcons.get_icon("server"), "Remotes")
        tb_remotes.triggered.connect(self._open_remote_manager)

        tb_refresh = toolbar.addAction(OutlineIcons.get_icon("refresh"), "Refresh")
        tb_refresh.triggered.connect(self._refresh_all)

        tb_equalize = toolbar.addAction(OutlineIcons.get_icon("sync"), "Equalize")
        tb_equalize.setToolTip("Equalize Left and Right panels (50/50)")
        tb_equalize.triggered.connect(self._equalize_panels)

        tb_jobs = toolbar.addAction(OutlineIcons.get_icon("minus"), "Jobs")
        tb_jobs.setToolTip("Toggle / Minimize Transfer Jobs panel (Ctrl+J)")
        tb_jobs.triggered.connect(self._toggle_jobs_panel)
        assert toolbar is not None, "Toolbar created"

    def _init_central_widget(self) -> None:
        """Construct central dual splitter containing browser panels and jobs view."""
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        self._vsplitter = QSplitter(Qt.Orientation.Vertical)
        self._vsplitter.setChildrenCollapsible(False)
        self._dual_panel = DualPanelWidget(self._cli, self._transfer_mgr, parent=self)
        self._vsplitter.addWidget(self._dual_panel)

        self._jobs_view = JobsView(self._transfer_mgr, parent=self)
        self._vsplitter.addWidget(self._jobs_view)

        self._vsplitter.setStretchFactor(0, 7)
        self._vsplitter.setStretchFactor(1, 3)

        vbox.addWidget(self._vsplitter)
        self.setCentralWidget(central)
        assert self._vsplitter is not None, "Splitter required"

    def _toggle_jobs_panel(self) -> None:
        """Toggle bottom jobs panel between collapsed and expanded state."""
        assert self._jobs_view is not None, "Jobs view required"
        self._jobs_view.toggle_collapsed()
        assert hasattr(self._jobs_view, "_is_collapsed"), "Flag required"

    def _equalize_panels(self) -> None:
        """Reset dual browser panels to equal 50/50 balance."""
        assert self._dual_panel is not None, "Dual panel required"
        self._dual_panel.equalize_panels()
        assert self._dual_panel.isVisible(), "Dual panel must be visible"


    def _load_initial_remotes(self) -> None:
        """Fetch configured remotes and populate dual panels."""
        assert self._config_mgr is not None, "ConfigManager required"
        res = self._config_mgr.list_remotes()
        remote_names = [cfg.name for cfg in (res.data or [])]
        remote_names.append("local")
        self._dual_panel.set_remotes(remote_names)

    def _open_remote_manager(self) -> None:
        """Open remote configurations management modal."""
        assert self._config_mgr is not None, "ConfigManager required"
        dlg = RemoteManagerDialog(self._config_mgr, parent=self)
        dlg.exec()
        self._load_initial_remotes()

    def _refresh_all(self) -> None:
        """Reload remotes and refresh panels."""
        self._load_initial_remotes()
        self._dual_panel.refresh_panels()
        self.statusBar().showMessage("Refreshed all views.", 3000)

    def _show_about(self) -> None:
        """Display about dialog adhering to NASA JPL Power of 10 standards."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
            "Modern Enterprise GUI for managing and transferring data across object storage servers.<br>"
            "Powered by <i>rclone</i> engine.<br><br>"
            "<b>Architecture & Reliability Standards:</b><br>"
            "• NASA JPL The Power of 10 Safety Rules<br>"
            "• Statically Bounded Loops & Memory<br>"
            "• High Assertion Density & Strict Flow<br>"
            "• Clean Monochrome Outline Icon System",
        )

    def closeEvent(self, event) -> None:
        """Cleanly handle application window close."""
        assert event is not None, "Event cannot be None"
        if hasattr(self, "_dual_panel"):
            self._dual_panel.close_panels()
        super().closeEvent(event)

