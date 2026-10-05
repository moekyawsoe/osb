"""Low-level execution engine for rclone CLI commands.

Adheres strictly to NASA JPL Power of 10 rules:
- Rule 1: Simple linear control flow
- Rule 2: Statically bounded loops
- Rule 3: Bounded memory and pipe buffers
- Rule 4: Functions under 60 lines
- Rule 5: High assertion density (>= 2 assertions per function)
- Rule 7: Strict checking of all return values
"""

import json
import os
import shutil
import subprocess
import time
from typing import List, Optional

from osb.core.constants import (
    DEFAULT_COMMAND_TIMEOUT_SEC,
    LIST_TIMEOUT_SEC,
    MAX_ITEMS_PER_DIR,
    MAX_OUTPUT_BUFFER_BYTES,
    MAX_SUBPROCESS_WAIT_TICKS,
    TEST_CONN_TIMEOUT_SEC,
)
from osb.core.logger import log_action, log_error
from osb.core.models import OperationResult, StorageItem
from osb.core.utils import build_rclone_target



from osb.core.rclone_detector import find_rclone_binary


class RcloneCli:
    """Safe execution wrapper for rclone commands with bounded execution."""

    def __init__(self, rclone_binary: Optional[str] = None) -> None:
        """Initialize and verify rclone binary location."""
        self._binary = find_rclone_binary(rclone_binary) or rclone_binary or "/usr/bin/rclone"
        assert self._binary is not None, "rclone binary path cannot be None"
        assert os.path.exists(self._binary), f"rclone not found at {self._binary}"

    def check_installed(self) -> OperationResult:
        """Verify rclone binary is functional and get version."""
        assert os.path.isfile(self._binary), "Binary must be a regular file"
        res = self.execute_command(["version"], timeout_sec=5)
        assert isinstance(res, OperationResult), "Must return OperationResult"
        return res

    def execute_command(
        self,
        args: List[str],
        timeout_sec: int = DEFAULT_COMMAND_TIMEOUT_SEC,
    ) -> OperationResult:
        """Execute rclone command with bounded timeout and buffer capture."""
        assert isinstance(args, list) and len(args) > 0, "Args must be non-empty list"
        assert timeout_sec > 0 and timeout_sec <= 300, "Timeout within [1, 300] sec"

        cmd = [self._binary] + args
        cmd_str = f"rclone {' '.join(args)}"
        log_action("RcloneCli", f"Executing: {cmd_str}")
        start_t = time.time()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            elapsed = time.time() - start_t
            stdout = proc.stdout[:MAX_OUTPUT_BUFFER_BYTES]
            stderr = proc.stderr[:MAX_OUTPUT_BUFFER_BYTES]

            if proc.returncode == 0:
                log_action("RcloneCli", f"Success ({elapsed:.2f}s): {cmd_str}")
                return OperationResult(success=True, message="Success", data=stdout)

            err_msg = stderr.strip() if stderr.strip() else f"Exit code {proc.returncode}"
            log_error("RcloneCli", f"Failed ({elapsed:.2f}s): {cmd_str} -> {err_msg[:200]}")
            return OperationResult(success=False, message=err_msg, data=stdout)
        except subprocess.TimeoutExpired:
            log_error("RcloneCli", f"Timeout ({timeout_sec}s): {cmd_str}")
            return OperationResult(success=False, message=f"Command timed out after {timeout_sec}s")
        except Exception as exc:
            log_error("RcloneCli", f"Exception on {cmd_str}: {str(exc)}")
            return OperationResult(success=False, message=f"Execution error: {str(exc)}")

    def test_connection(self, remote: str) -> OperationResult:
        """Test reachability of an object storage remote."""
        assert isinstance(remote, str) and len(remote) > 0, "Remote must be specified"
        target = build_rclone_target(remote, "")
        assert ":" in target or target.startswith("/"), "Target must be formatted"

        log_action("RcloneCli", f"Testing connection to remote '{remote}'...")
        args = ["lsd", target, "--timeout", f"{TEST_CONN_TIMEOUT_SEC}s", "--max-depth", "1"]
        res = self.execute_command(args, timeout_sec=TEST_CONN_TIMEOUT_SEC + 5)
        if res.success:
            log_action("RcloneCli", f"Connection verified for '{remote}'")
            return OperationResult(success=True, message=f"Connection to '{remote}' verified.")
        log_error("RcloneCli", f"Connection test failed for '{remote}': {res.message[:150]}")
        return OperationResult(success=False, message=f"Connection failed: {res.message}")


    def list_items(self, remote: str, path: str) -> OperationResult:
        """List items inside a remote bucket or directory as structured StorageItems."""
        assert isinstance(remote, str), "Remote must be string"
        assert isinstance(path, str), "Path must be string"

        target = build_rclone_target(remote, path)
        args = ["lsjson", target, "--max-depth", "1", "--stat=false"]
        res = self.execute_command(args, timeout_sec=LIST_TIMEOUT_SEC)
        if not res.success:
            return self._handle_list_fallback(remote, path, res.message)

        return self._parse_lsjson(res.data or "[]", remote, path)

    def _handle_list_fallback(self, remote: str, path: str, err_msg: str) -> OperationResult:
        """Fallback for remote root bucket listing when lsjson requires lsd."""
        assert isinstance(remote, str), "Remote must be string"
        assert isinstance(err_msg, str), "Error message must be string"

        target = build_rclone_target(remote, path)
        args = ["lsd", target, "--timeout", "15s"]
        lsd_res = self.execute_command(args, timeout_sec=15)
        if not lsd_res.success:
            return OperationResult(success=False, message=err_msg)

        items: List[StorageItem] = []
        raw_lines = (lsd_res.data or "").splitlines()
        max_lines = min(len(raw_lines), MAX_ITEMS_PER_DIR)

        # NASA Rule 2: Fixed bounded iteration
        for i in range(max_lines):
            line = raw_lines[i].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 5:
                bucket_name = parts[-1]
                items.append(
                    StorageItem(
                        name=bucket_name,
                        path=bucket_name,
                        size=0,
                        is_dir=True,
                        is_bucket=True,
                    )
                )

        return OperationResult(success=True, message="Fallback listing OK", data=items)

    def _parse_lsjson(self, raw_json: str, remote: str, base_path: str) -> OperationResult:
        """Parse rclone lsjson structured array with static upper bound."""
        assert isinstance(raw_json, str), "raw_json must be string"
        assert isinstance(remote, str), "remote must be string"

        try:
            data = json.loads(raw_json)
            if not isinstance(data, list):
                return OperationResult(success=False, message="lsjson returned non-list data")

            items: List[StorageItem] = []
            bound_count = min(len(data), MAX_ITEMS_PER_DIR)
            is_root = (base_path.strip("/") == "")

            # NASA Rule 2: Fixed bounded loop
            for i in range(bound_count):
                entry = data[i]
                name = str(entry.get("Name", ""))
                if not name:
                    continue
                is_dir = bool(entry.get("IsDir", False))
                item_path = f"{base_path.rstrip('/')}/{name}".lstrip("/") if base_path else name
                raw_size = int(entry.get("Size", 0))
                item = StorageItem(
                    name=name,
                    path=item_path,
                    size=max(0, raw_size) if is_dir else raw_size,
                    is_dir=is_dir,
                    is_bucket=is_root and is_dir,
                    mod_time=str(entry.get("ModTime", "")),
                    mime_type=str(entry.get("MimeType", "")),
                )
                items.append(item)

            return OperationResult(success=True, message="Listed successfully", data=items)
        except json.JSONDecodeError as err:
            return OperationResult(success=False, message=f"JSON parse error: {str(err)}")

    def make_bucket_or_dir(self, remote: str, path: str) -> OperationResult:
        """Create a bucket or directory on the target remote."""
        assert isinstance(remote, str) and len(remote) > 0, "Remote must be non-empty"
        assert isinstance(path, str) and len(path) > 0, "Path must be non-empty"

        target = build_rclone_target(remote, path)
        res = self.execute_command(["mkdir", target], timeout_sec=20)
        assert isinstance(res, OperationResult), "Must return OperationResult"
        return res

    def delete_item(self, remote: str, path: str, is_dir: bool, purge: bool = False) -> OperationResult:
        """Safely delete an object, directory, or bucket."""
        assert isinstance(remote, str) and len(remote) > 0, "Remote must be non-empty"
        assert isinstance(path, str) and len(path) > 0, "Path must be non-empty"

        target = build_rclone_target(remote, path)
        if is_dir:
            cmd = ["purge", target] if purge else ["rmdir", target]
        else:
            cmd = ["deletefile", target]

        res = self.execute_command(cmd, timeout_sec=30)
        assert isinstance(res, OperationResult), "Must return OperationResult"
        return res

    def get_size_stats(self, remote: str, path: str) -> OperationResult:
        """Retrieve total object count and aggregated byte size."""
        assert isinstance(remote, str), "Remote must be string"
        assert isinstance(path, str), "Path must be string"

        target = build_rclone_target(remote, path)
        res = self.execute_command(["size", target, "--json"], timeout_sec=30)
        if not res.success:
            return res

        try:
            stats = json.loads(res.data or "{}")
            return OperationResult(success=True, message="Stats retrieved", data=stats)
        except json.JSONDecodeError as err:
            return OperationResult(success=False, message=f"Stats parse error: {str(err)}")

    def get_hash(self, remote: str, path: str, hash_type: str = "md5") -> OperationResult:
        """Compute checksum (md5/sha1) for an object storage item."""
        assert isinstance(remote, str) and len(remote) > 0, "Remote must be specified"
        assert hash_type in ("md5", "sha1", "sha256"), "Supported hash type required"

        target = build_rclone_target(remote, path)
        res = self.execute_command(["hashsum", hash_type, target], timeout_sec=25)
        if not res.success:
            return res

        output = (res.data or "").strip()
        parts = output.split()
        hash_val = parts[0] if parts else "N/A"
        return OperationResult(success=True, message="Hash computed", data=hash_val)
