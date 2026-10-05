"""Unit tests for models and data structures adhering to NASA JPL Power of 10."""

import unittest
from osb.core.models import (
    JobStatus,
    OperationResult,
    RemoteConfig,
    StorageItem,
    TransferJob,
    TransferOperation,
)


class TestModels(unittest.TestCase):
    """Test data invariants and assertion enforcement."""

    def test_storage_item_valid(self) -> None:
        """Verify normal creation of StorageItem."""
        item = StorageItem(
            name="test-file.txt",
            path="bucket/test-file.txt",
            size=1024,
            is_dir=False,
            mod_time="2026-10-05T10:00:00Z",
        )
        self.assertEqual(item.name, "test-file.txt")
        self.assertEqual(item.size, 1024)
        self.assertFalse(item.is_dir)

    def test_storage_item_invalid_size(self) -> None:
        """NASA Rule 5 assertion failure on negative size."""
        with self.assertRaises(AssertionError):
            StorageItem(name="bad.txt", path="bad.txt", size=-10, is_dir=False)

    def test_storage_item_invalid_name(self) -> None:
        """NASA Rule 5 assertion failure on empty name."""
        with self.assertRaises(AssertionError):
            StorageItem(name="", path="bad.txt", size=10, is_dir=False)

    def test_remote_config_valid(self) -> None:
        """Verify valid remote config creation."""
        cfg = RemoteConfig(
            name="my-minio",
            type="s3",
            provider="Minio",
            endpoint="http://127.0.0.1:9000",
            access_key_id="admin",
            secret_access_key="password",
        )
        self.assertEqual(cfg.name, "my-minio")
        self.assertTrue(cfg.force_path_style)

    def test_remote_config_invalid_name(self) -> None:
        """Verify assertion failure on empty remote name."""
        with self.assertRaises(AssertionError):
            RemoteConfig(name="", type="s3")

    def test_transfer_job_valid(self) -> None:
        """Verify TransferJob lifecycle properties."""
        job = TransferJob(
            job_id="job-101",
            op=TransferOperation.COPY,
            src_remote="s3-src",
            src_path="data/",
            dst_remote="s3-dst",
            dst_path="backup/",
        )
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertEqual(job.bytes_transferred, 0)
        self.assertEqual(job.percentage, 0.0)

    def test_operation_result_valid(self) -> None:
        """Verify OperationResult container."""
        res = OperationResult(success=True, message="All good", data={"key": "val"})
        self.assertTrue(res.success)
        self.assertEqual(res.message, "All good")


if __name__ == "__main__":
    unittest.main()
