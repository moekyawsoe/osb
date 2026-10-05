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
        for worker in list(self.mgr._active_workers.values()):
            worker.cancel()
            worker.wait(1000)
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
        worker = self.mgr._active_workers.get(job.job_id)
        if worker:
            worker.cancel()
            worker.wait(1000)

    def test_cancel_nonexistent_job(self) -> None:
        """Verify cancelling non-existent job fails safely."""
        res = self.mgr.cancel_job("invalid-job-id")
        self.assertFalse(res.success)

    def test_job_current_file_progress(self) -> None:
        """Verify current_file updates through worker progress and completion."""
        res = self.mgr.submit_job(
            TransferOperation.MOVE,
            "local",
            self.test_src,
            "local",
            self.test_dst,
        )
        self.assertTrue(res.success)
        job = res.data
        self.assertEqual(job.current_file, "")
        worker = self.mgr._active_workers.get(job.job_id)
        if worker:
            worker.cancel()
            worker.wait(1000)

        self.mgr._on_worker_progress(job.job_id, 1024, 2048, 50.0, "2 MB/s", "1s", "image.png")
        self.assertEqual(job.current_file, "image.png")
        self.assertEqual(job.percentage, 50.0)

        self.mgr._on_worker_finished(job.job_id, True, "Completed successfully")
        self.assertEqual(job.current_file, "Completed")
        self.assertEqual(job.status, JobStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()
