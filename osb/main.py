"""Application entry point for Object Storage Bridge.

Complies with NASA JPL Power of 10 rules.
"""

import argparse
import signal
import sys
from typing import List, Optional
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from osb.core.config_mgr import ConfigManager
from osb.core.constants import APP_NAME
from osb.core.rclone_cli import RcloneCli
from osb.core.rclone_detector import find_rclone_binary
from osb.core.transfer_mgr import TransferManager
from osb.gui.main_window import MainWindow
from osb.gui.rclone_dialog import RcloneSetupDialog
from osb.gui.theme import apply_enterprise_theme


def setup_cli_parser() -> argparse.ArgumentParser:
    """Construct command line arguments parser."""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} - Enterprise GUI for Object Storage")
    parser.add_argument("--rclone", type=str, default=None, help="Custom path to rclone binary")
    return parser


def run_app(argv: Optional[List[str]] = None) -> int:
    """Initialize environment, verify dependencies, and start Qt event loop."""
    parser = setup_cli_parser()
    args = parser.parse_args(argv)

    app = QApplication(sys.argv if argv is None else ["osb"] + argv)
    app.setApplicationName(APP_NAME)
    apply_enterprise_theme(app)

    # Enable Ctrl+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    binary = find_rclone_binary(args.rclone)
    if not binary:
        dlg = RcloneSetupDialog(custom_path=args.rclone)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return 1
        binary = dlg.get_detected_binary() or find_rclone_binary()
        if not binary:
            return 1

    try:
        cli = RcloneCli(rclone_binary=binary)
        chk = cli.check_installed()
        if not chk.success:
            QMessageBox.critical(None, "Rclone Error", f"Failed to execute rclone:\n{chk.message}")
            return 1
    except Exception as exc:
        QMessageBox.critical(None, "Initialization Error", f"Fatal error during init:\n{str(exc)}")
        return 1

    config_mgr = ConfigManager(cli)
    transfer_mgr = TransferManager(cli._binary)

    window = MainWindow(cli, config_mgr, transfer_mgr)
    window.show()

    return app.exec()


def main() -> None:
    """CLI launcher entrypoint."""
    sys.exit(run_app())


if __name__ == "__main__":
    main()
