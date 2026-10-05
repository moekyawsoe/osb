"""Unit tests for procedural monochrome outline vector icons."""

import unittest
from PyQt6.QtWidgets import QApplication
from osb.gui.outline_icons import OutlineIcons

# Ensure QApplication is initialized for QPixmap/QPainter
app = QApplication.instance() or QApplication([])


class TestOutlineIcons(unittest.TestCase):
    """Verify outline icons render with non-null pixmaps and caching."""

    def test_render_all_icon_types(self) -> None:
        """Verify all supported outline icon names render without failure."""
        icon_names = [
            "bucket", "server", "folder", "folder_plus", "file",
            "arrow_right", "arrow_left", "arrow_up", "refresh", "sync",
            "copy", "move", "move_left", "trash", "plus", "minus", "check", "cross",
            "search", "settings", "info", "stop", "play",
        ]

        for name in icon_names:
            pix = OutlineIcons.render_pixmap(name, size=24, color_hex="#d1d5db")
            self.assertFalse(pix.isNull(), f"Icon '{name}' produced null pixmap")
            self.assertEqual(pix.width(), 24)
            self.assertEqual(pix.height(), 24)

    def test_icon_caching(self) -> None:
        """Verify icons are cached across calls."""
        icon1 = OutlineIcons.get_icon("bucket", size=20)
        icon2 = OutlineIcons.get_icon("bucket", size=20)
        self.assertIsNotNone(icon1)
        self.assertEqual(icon1, icon2)


if __name__ == "__main__":
    unittest.main()
