"""System-wide constants and bounds compliant with NASA JPL Power of 10 rules.

All limits are fixed upper bounds to guarantee bounded memory and execution.
"""

from typing import Final

# NASA Rule 2: Statically determinable fixed upper bounds for loops
MAX_ITEMS_PER_DIR: Final[int] = 10000
MAX_REMOTE_COUNT: Final[int] = 128
MAX_SUBPROCESS_WAIT_TICKS: Final[int] = 1200  # 1200 * 50ms = 60s
MAX_STATS_PARSE_LINES: Final[int] = 10000
MAX_LOOP_ITERATIONS: Final[int] = 50000
MAX_PATH_DEPTH: Final[int] = 64

# NASA Rule 3: Fixed bounds on queues, logs, and memory buffers
MAX_TRANSFER_QUEUE_SIZE: Final[int] = 200
MAX_JOB_HISTORY_SIZE: Final[int] = 500
MAX_LOG_ENTRIES: Final[int] = 1000
MAX_OUTPUT_BUFFER_BYTES: Final[int] = 2 * 1024 * 1024  # 2MB
MAX_LINE_BUFFER_CHARS: Final[int] = 4096

# Timeouts in seconds
DEFAULT_COMMAND_TIMEOUT_SEC: Final[int] = 30
TEST_CONN_TIMEOUT_SEC: Final[int] = 15
LIST_TIMEOUT_SEC: Final[int] = 45

# Concurrency limits
DEFAULT_CONCURRENT_TRANSFERS: Final[int] = 4
MAX_CONCURRENT_TRANSFERS: Final[int] = 16
MIN_CONCURRENT_TRANSFERS: Final[int] = 1

# Supported Object Storage Providers
PROVIDER_S3: Final[str] = "s3"
PROVIDER_B2: Final[str] = "b2"
PROVIDER_GCS: Final[str] = "google cloud storage"
PROVIDER_AZURE: Final[str] = "azureblob"
PROVIDER_SWIFT: Final[str] = "swift"
PROVIDER_LOCAL: Final[str] = "local"
PROVIDER_SFTP: Final[str] = "sftp"

# Application Metadata
APP_NAME: Final[str] = "OSB - Object Storage Bridge"
APP_VERSION: Final[str] = "1.0.0"
