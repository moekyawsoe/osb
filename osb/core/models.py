"""Data models for object storage items, remotes, and background jobs.

Complies with NASA JPL Rule 9 (unambiguous structures) and Rule 5 (assertions).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import time


class TransferOperation(Enum):
    """Supported transfer operations between storage endpoints."""
    COPY = "copy"
    MOVE = "move"
    SYNC = "sync"


class JobStatus(Enum):
    """Lifecycle states of a background transfer job."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class StorageItem:
    """Represents a file, folder, or bucket on an object storage server."""
    name: str
    path: str
    size: int
    is_dir: bool
    is_bucket: bool = False
    mod_time: str = ""
    mime_type: str = ""
    etag: str = ""

    def __post_init__(self) -> None:
        """NASA Rule 5: Validate invariant properties upon construction."""
        assert isinstance(self.name, str) and len(self.name) > 0, "Name must be non-empty"
        assert self.size >= 0, "Size must be non-negative"


@dataclass
class RemoteConfig:
    """Configuration definition for an rclone storage remote."""
    name: str
    type: str
    provider: str = ""
    endpoint: str = ""
    region: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    force_path_style: bool = True
    env_auth: bool = False
    extra_params: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """NASA Rule 5: Verify valid remote configuration invariants."""
        assert isinstance(self.name, str) and len(self.name) > 0, "Remote name must be non-empty"
        assert isinstance(self.type, str) and len(self.type) > 0, "Remote type must be non-empty"


@dataclass
class TransferJob:
    """Tracks state and progress of an asynchronous transfer job."""
    job_id: str
    op: TransferOperation
    src_remote: str
    src_path: str
    dst_remote: str
    dst_path: str
    status: JobStatus = JobStatus.QUEUED
    bytes_transferred: int = 0
    total_bytes: int = 0
    percentage: float = 0.0
    speed_str: str = "0 B/s"
    eta_str: str = "--"
    error_message: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    log_lines: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """NASA Rule 5: Verify valid job state upon initialization."""
        assert isinstance(self.job_id, str) and len(self.job_id) > 0, "Job ID must be non-empty"
        assert self.bytes_transferred >= 0, "Bytes transferred cannot be negative"


@dataclass(frozen=True)
class OperationResult:
    """Safe return container for non-void operations (NASA Rule 7)."""
    success: bool
    message: str = ""
    data: Optional[object] = None

    def __post_init__(self) -> None:
        """NASA Rule 5: Verify validity of the operation result."""
        assert isinstance(self.success, bool), "Success flag must be boolean"
        assert isinstance(self.message, str), "Message must be string"
