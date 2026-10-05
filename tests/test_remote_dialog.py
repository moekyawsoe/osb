"""Unit tests for TestConnWorker and remote connection crash prevention.

Complies with NASA JPL Power of 10 rules.
"""

import unittest
from unittest.mock import MagicMock
from PyQt6.QtCore import QCoreApplication

from osb.core.config_mgr import ConfigManager
from osb.core.models import OperationResult
from osb.gui.remote_dialog import TestConnWorker


class TestRemoteWorkers(unittest.TestCase):
    """Test background worker stability and cancellation."""

    @classmethod
    def setUpClass(cls) -> None:
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()

    def test_worker_success(self) -> None:
        """Verify normal test execution and signal emission."""
        mock_mgr = MagicMock(spec=ConfigManager)
        mock_mgr.test_remote.return_value = OperationResult(success=True, message="Connected OK")

        worker = TestConnWorker(mock_mgr, "test-s3")
        results = []
        worker.test_result.connect(lambda ok, msg: results.append((ok, msg)))

        worker.run()
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][0])
        self.assertIn("Connected OK", results[0][1])

    def test_worker_exception_resilience(self) -> None:
        """Verify that exceptions during test_remote do not crash the app or thread."""
        mock_mgr = MagicMock(spec=ConfigManager)
        mock_mgr.test_remote.side_effect = RuntimeError("Subprocess pipe broken")

        worker = TestConnWorker(mock_mgr, "faulty-remote")
        results = []
        worker.test_result.connect(lambda ok, msg: results.append((ok, msg)))

        worker.run()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])
        self.assertIn("Subprocess pipe broken", results[0][1])

    def test_worker_stop_cancellation(self) -> None:
        """Verify that stopped worker suppresses signal emission."""
        mock_mgr = MagicMock(spec=ConfigManager)
        mock_mgr.test_remote.return_value = OperationResult(success=True, message="Connected OK")

        worker = TestConnWorker(mock_mgr, "test-s3")
        worker.stop()

        results = []
        worker.test_result.connect(lambda ok, msg: results.append((ok, msg)))

        worker.run()
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
