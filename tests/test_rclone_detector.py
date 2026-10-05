"""Unit tests for rclone detector, platform guides, and installation dialog.

Complies with NASA JPL Power of 10 rules.
"""

import os
import unittest
from PyQt6.QtWidgets import QApplication

from osb.core.rclone_detector import (
    OFFICIAL_DOWNLOADS_URL,
    OFFICIAL_INSTALL_GUIDE_URL,
    PLATFORM_GUIDES,
    find_rclone_binary,
    get_current_platform_key,
    get_platform_guide,
)
from osb.gui.rclone_dialog import RcloneSetupDialog

app = QApplication.instance() or QApplication([])


class TestRcloneDetector(unittest.TestCase):
    """Verify rclone detection and cross-platform metadata."""

    def test_find_rclone_binary(self) -> None:
        """Verify binary detection on the current host system."""
        binary = find_rclone_binary()
        self.assertIsNotNone(binary)
        self.assertTrue(os.path.isfile(binary))
        self.assertTrue(os.access(binary, os.X_OK))

    def test_find_rclone_binary_invalid_custom(self) -> None:
        """Verify fallback behavior when invalid custom path is provided."""
        # Non-existent path returns default or None
        binary = find_rclone_binary(custom_path="/path/that/does/not/exist/rclone")
        # Since host has rclone installed, it should fallback to system rclone
        self.assertIsNotNone(binary)

    def test_platform_guides_data(self) -> None:
        """Verify all supported platforms have valid download and install guides."""
        expected_platforms = ["linux", "darwin", "windows"]
        for plat in expected_platforms:
            self.assertIn(plat, PLATFORM_GUIDES)
            guide = get_platform_guide(plat)
            self.assertGreater(len(guide.methods), 0)
            self.assertTrue(guide.download_url.startswith("http"))
            self.assertTrue(guide.guide_url.startswith("http"))
            for m in guide.methods:
                self.assertGreater(len(m.title), 0)
                self.assertGreater(len(m.command), 0)

    def test_current_platform_key(self) -> None:
        """Verify platform key detection returns valid identifier."""
        key = get_current_platform_key()
        self.assertIn(key, ("linux", "darwin", "windows"))

    def test_rclone_setup_dialog_instantiation(self) -> None:
        """Verify RcloneSetupDialog initializes cleanly."""
        dlg = RcloneSetupDialog()
        self.assertIsNotNone(dlg)
        self.assertGreaterEqual(dlg._tabs.count(), 3)
        dlg.close()


if __name__ == "__main__":
    unittest.main()
