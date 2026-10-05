"""Unit tests for background transfer job manager."""

import os
import shutil
import tempfile
import unittest
from PyQt6.QtWidgets import QApplication
from osb.core.models import JobStatus, TransferOperation
from osb.core.transfer_mgr import TransferManager

app = QApplication.instance() or QApplication([])


class TestTransferManager(unittest.TestCase):
    """Verify job queuing, metrics tracking, and cancellation."""

    def setUp(self) -> None:
        self.mgr = TransferManager()
        self.test_src = tempfile.mkdtemp(prefix="osb_src_")
        self.test_dst = tempfile.mkdtemp(prefix="osb_dst_")

    def tearDown(self) -> None:
        if os.path.exists(self.test_src):
            shutil.rmtree(self.test_src)
        if os.path.exists(self.test_dst):
            shutil.rmtree(self.test_dst)

    def test_submit_job(self) -> None:
        """Verify submitting job adds it to tracked collection."""
        res = self.mgr.submit_job(
            TransferOperation.COPY,
            "local",
            self.test_src,
            "local",
            self.test_dst,
        )
        self.assertTrue(res.success)
        job = res.data
        self.assertIsNotNone(job)
        self.assertEqual(job.src_path, self.test_src)
        self.assertEqual(job.dst_path, self.test_dst)

    def test_cancel_nonexistent_job(self) -> None:
        """Verify cancelling non-existent job fails safely."""
        res = self.mgr.cancel_job("invalid-job-id")
        self.assertFalse(res.success)


if __name__ == "__main__":
    unittest.main()
