"""Unit tests for formatting, parsing, and validation utilities."""

import unittest
from osb.core.utils import (
    build_rclone_target,
    format_bytes,
    format_rate,
    is_valid_bucket_name,
    parse_rclone_target,
)


class TestUtils(unittest.TestCase):
    """Test safety bounds and correct transformation of utilities."""

    def test_format_bytes(self) -> None:
        """Verify human-readable byte calculations."""
        self.assertEqual(format_bytes(0), "0.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(5 * 1024 * 1024 * 1024), "5.00 GB")

    def test_format_rate(self) -> None:
        """Verify transfer rate formatting."""
        self.assertEqual(format_rate(0.0), "0 B/s")
        self.assertEqual(format_rate(1500000.0), "1.43 MB/s")

    def test_build_rclone_target(self) -> None:
        """Verify rclone remote:path builder."""
        self.assertEqual(build_rclone_target("minio", "bucket/data"), "minio:bucket/data")
        self.assertEqual(build_rclone_target("minio:", "/bucket/data/"), "minio:bucket/data/")
        self.assertEqual(build_rclone_target("local", "/var/data"), "/var/data")
        self.assertEqual(build_rclone_target("", "data"), "data")

    def test_parse_rclone_target(self) -> None:
        """Verify extracting remote and path."""
        remote, path = parse_rclone_target("s3-prod:my-bucket/logs")
        self.assertEqual(remote, "s3-prod")
        self.assertEqual(path, "my-bucket/logs")

        remote2, path2 = parse_rclone_target("/local/storage")
        self.assertEqual(remote2, "local")
        self.assertEqual(path2, "/local/storage")

    def test_is_valid_bucket_name(self) -> None:
        """Verify S3 DNS compliant bucket name validation."""
        valid, msg = is_valid_bucket_name("my-storage-bucket-01")
        self.assertTrue(valid)

        invalid_short, msg = is_valid_bucket_name("ab")
        self.assertFalse(invalid_short)

        invalid_upper, msg = is_valid_bucket_name("MyBucket")
        self.assertFalse(invalid_upper)

        invalid_dots, msg = is_valid_bucket_name("my..bucket")
        self.assertFalse(invalid_dots)


if __name__ == "__main__":
    unittest.main()
