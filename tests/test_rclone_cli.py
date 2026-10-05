"""Unit tests for low-level rclone CLI wrapper."""

import os
import shutil
import tempfile
import unittest
from osb.core.rclone_cli import RcloneCli


class TestRcloneCli(unittest.TestCase):
    """Verify rclone commands execution against real temporary directories."""

    def setUp(self) -> None:
        self.cli = RcloneCli()
        self.test_dir = tempfile.mkdtemp(prefix="osb_cli_test_")

    def tearDown(self) -> None:
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_installed(self) -> None:
        """Verify rclone is discovered and version string is returned."""
        res = self.cli.check_installed()
        self.assertTrue(res.success)
        self.assertIn("rclone", (res.data or "").lower())

    def test_list_items_empty(self) -> None:
        """Verify listing an empty directory returns empty list."""
        res = self.cli.list_items("local", self.test_dir)
        self.assertTrue(res.success)
        self.assertEqual(res.data, [])

    def test_list_items_with_files(self) -> None:
        """Verify listing directory with files and subdirectories."""
        file_path = os.path.join(self.test_dir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("NASA JPL Power of 10")

        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir)

        res = self.cli.list_items("local", self.test_dir)
        self.assertTrue(res.success)
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 2)

        names = {item.name for item in res.data}
        self.assertIn("test.txt", names)
        self.assertIn("subdir", names)

    def test_make_bucket_or_dir(self) -> None:
        """Verify directory creation via rclone mkdir."""
        target_path = os.path.join(self.test_dir, "new_folder")
        res = self.cli.make_bucket_or_dir("local", target_path)
        self.assertTrue(res.success)
        self.assertTrue(os.path.exists(target_path))

    def test_get_size_stats(self) -> None:
        """Verify size stats calculation."""
        file_path = os.path.join(self.test_dir, "sample.bin")
        with open(file_path, "wb") as f:
            f.write(b"0" * 1024)

        res = self.cli.get_size_stats("local", self.test_dir)
        self.assertTrue(res.success)
        self.assertEqual(res.data.get("count"), 1)
        self.assertEqual(res.data.get("bytes"), 1024)


if __name__ == "__main__":
    unittest.main()
