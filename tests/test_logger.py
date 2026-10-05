"""Unit tests for ActionLogger and LogSignalEmitter.

Complies with NASA JPL Power of 10 rules.
"""

import os
import tempfile
import unittest
from PyQt6.QtCore import QCoreApplication

from osb.core.logger import ActionLogger, LogSignalEmitter, log_action, log_error


class TestActionLogger(unittest.TestCase):
    """Test suite for ActionLogger and signal emission."""

    @classmethod
    def setUpClass(cls) -> None:
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.logger = ActionLogger(log_dir=self.tmp_dir)

    def test_logger_file_creation(self) -> None:
        """Verify that log file is created in target directory."""
        log_file = os.path.join(self.tmp_dir, "osb_actions.log")
        self.logger.log("INFO", "UnitTest", "Hello logging world")
        self.assertTrue(os.path.exists(log_file))

        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Hello logging world", content)
        self.assertIn("[UnitTest]", content)

    def test_memory_history_and_signals(self) -> None:
        """Verify ring buffer history and signal emission."""
        received = []

        def slot(ts, lvl, msg):
            received.append((lvl, msg))

        emitter = ActionLogger.get_emitter()
        emitter.log_emitted.connect(slot)

        self.logger.log("WARNING", "TestModule", "Something might be wrong")
        self.logger.log("ERROR", "TestModule", "Critical breakdown")

        hist = self.logger.get_history()
        self.assertGreaterEqual(len(hist), 2)
        self.assertTrue(any("Something might be wrong" in h for h in hist))
        self.assertTrue(any("Critical breakdown" in h for h in hist))

        emitter.log_emitted.disconnect(slot)


if __name__ == "__main__":
    unittest.main()
