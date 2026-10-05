"""Utility functions for size formatting, path normalization, and validation.

Adheres strictly to NASA JPL Power of 10 rules.
"""

import re
from typing import Tuple


def format_bytes(size_bytes: int) -> str:
    """Format byte count into human-readable representation with fixed bounds."""
    assert isinstance(size_bytes, int), "size_bytes must be integer"
    assert size_bytes >= 0, "size_bytes must be non-negative"

    units = ("B", "KB", "MB", "GB", "TB", "PB")
    size_float = float(size_bytes)
    unit_idx = 0

    # NASA Rule 2: Fixed upper bound on loop
    for _ in range(len(units) - 1):
        if size_float < 1024.0:
            break
        size_float /= 1024.0
        unit_idx += 1

    formatted = f"{size_float:.2f} {units[unit_idx]}"
    assert len(formatted) > 0, "Formatted output must not be empty"
    return formatted


def format_rate(bytes_per_sec: float) -> str:
    """Format transfer speed into human-readable speed with bounds."""
    assert isinstance(bytes_per_sec, (int, float)), "Rate must be numeric"
    assert bytes_per_sec >= 0.0, "Rate must be non-negative"

    if bytes_per_sec < 1.0:
        return "0 B/s"
    formatted = f"{format_bytes(int(bytes_per_sec))}/s"
    assert len(formatted) > 0, "Formatted rate must not be empty"
    return formatted


def build_rclone_target(remote: str, path: str) -> str:
    """Construct a clean rclone target string like 'myremote:bucket/prefix'."""
    assert isinstance(remote, str), "Remote must be a string"
    assert isinstance(path, str), "Path must be a string"

    clean_remote = remote.strip().rstrip(":")
    is_local = (not clean_remote or clean_remote == "local")

    if is_local:
        result = path.strip() if path.strip() else "/"
    else:
        clean_path = path.strip().lstrip("/")
        result = f"{clean_remote}:{clean_path}"

    assert len(result) > 0, "Target string must be non-empty"
    return result



def parse_rclone_target(target: str) -> Tuple[str, str]:
    """Extract remote name and path components from an rclone string."""
    assert isinstance(target, str), "Target must be string"
    assert len(target) > 0, "Target cannot be empty string"

    if ":" in target:
        parts = target.split(":", 1)
        remote = parts[0].strip()
        path = parts[1].strip()
    else:
        remote = "local"
        path = target.strip()

    assert remote is not None, "Parsed remote must not be None"
    assert path is not None, "Parsed path must not be None"
    return remote, path


def is_valid_bucket_name(name: str) -> Tuple[bool, str]:
    """Validate S3-compatible bucket name according to standard DNS rules."""
    assert isinstance(name, str), "Bucket name must be string"
    assert len(name) <= 256, "Bucket name exceeds sanity bound"

    if len(name) < 3 or len(name) > 63:
        return False, "Bucket name must be between 3 and 63 characters long"

    pattern = r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$"
    if not re.match(pattern, name):
        return False, "Bucket names can only contain lowercase letters, numbers, hyphens, and periods"

    if ".." in name or ".-" in name or "-." in name:
        return False, "Bucket name cannot contain consecutive periods or mixed delimiters"

    return True, "Valid bucket name"
