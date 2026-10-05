"""Enterprise modern clean theme styling for PyQt6.

Strictly complies with the constraint:
- Zero gradients
- Monochrome slate enterprise aesthetic
- Clean outline borders and high contrast
- Functions <= 60 lines, >= 2 assertions per function
"""

from typing import Final
from PyQt6.QtWidgets import QApplication

ENTERPRISE_QSS: Final[str] = """
/* Enterprise Clean Monochrome QSS */

QWidget {
    background-color: #141518;
    color: #e5e7eb;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #383d46;
    selection-color: #ffffff;
    border: none;
}

QMainWindow, QDialog {
    background-color: #141518;
}

QMenuBar {
    background-color: #1a1c20;
    color: #d1d5db;
    border-bottom: 1px solid #2b2e35;
    padding: 2px 6px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #272a31;
    color: #ffffff;
}

QMenu {
    background-color: #1c1e23;
    border: 1px solid #333842;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #2c3038;
    color: #ffffff;
}

QToolBar {
    background-color: #1a1c20;
    border-bottom: 1px solid #2b2e35;
    spacing: 6px;
    padding: 6px 10px;
}

QToolButton {
    background-color: #22252b;
    border: 1px solid #353a44;
    border-radius: 4px;
    padding: 6px 12px;
    color: #e5e7eb;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #2c3038;
    border: 1px solid #4a505e;
}

QToolButton:pressed {
    background-color: #17181c;
}

QPushButton {
    background-color: #22252b;
    border: 1px solid #353a44;
    border-radius: 4px;
    padding: 6px 14px;
    color: #e5e7eb;
    font-weight: 500;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #2c3038;
    border: 1px solid #4a505e;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #181a1e;
}

QPushButton:disabled {
    background-color: #18191d;
    border: 1px solid #282a30;
    color: #555a64;
}

QLineEdit, QComboBox {
    background-color: #1b1d22;
    border: 1px solid #333842;
    border-radius: 4px;
    padding: 6px 10px;
    color: #f3f4f6;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #717786;
    background-color: #202228;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QHeaderView::section {
    background-color: #191b1f;
    color: #9ca3af;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #2d313a;
    border-right: 1px solid #22242a;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}

QTableView, QTableWidget, QTreeView {
    background-color: #1c1e23;
    alternate-background-color: #191a1f;
    border: 1px solid #2b2e36;
    border-radius: 4px;
    gridline-color: #272a31;
    color: #f3f4f6;
}

QTableView::item {
    padding: 4px 6px;
    border-bottom: 1px solid #24272e;
}

QTableView::item:selected {
    background-color: #333742;
    color: #ffffff;
}

QTableView::item:hover {
    background-color: #272a31;
}

QProgressBar {
    background-color: #191a1e;
    border: 1px solid #333842;
    border-radius: 3px;
    text-align: center;
    color: #f3f4f6;
    font-size: 11px;
    font-weight: bold;
    height: 14px;
}

QProgressBar::chunk {
    background-color: #9ca3af;
    border-radius: 2px;
}

QSplitter::handle {
    background-color: #252830;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QScrollBar:vertical {
    background-color: #141518;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #333842;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a505e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QTabWidget::pane {
    border: 1px solid #2b2e36;
    background-color: #1c1e23;
}

QTabBar::tab {
    background-color: #18191d;
    border: 1px solid #2b2e36;
    border-bottom: none;
    padding: 6px 14px;
    color: #9ca3af;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1c1e23;
    color: #ffffff;
    border-top: 2px solid #d1d5db;
}

QGroupBox {
    border: 1px solid #2f333c;
    border-radius: 5px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #9ca3af;
}

QStatusBar {
    background-color: #16171b;
    border-top: 1px solid #26282f;
    color: #9ca3af;
    font-size: 12px;
}
"""


def apply_enterprise_theme(app: QApplication) -> None:
    """Apply modern clean enterprise stylesheet to the application."""
    assert app is not None, "Application instance cannot be None"
    assert isinstance(app, QApplication), "Must be QApplication instance"
    app.setStyleSheet(ENTERPRISE_QSS)
