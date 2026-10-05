# OSB — Object Storage Bridge

An enterprise-grade, clean monochrome Python GUI for managing data across heterogeneous object storage servers, powered by the `rclone` engine and built strictly in accordance with **NASA JPL The Power of 10 Safety-Critical Rules**.

---

## Key Features

1. **GUI-Based Rclone Configuration Management**
   - Interactive management of all rclone remotes (`rclone config dump` / `create` / `delete`).
   - Built-in provider presets:
     - MinIO Server (S3-Compatible)
     - Amazon Web Services (AWS S3)
     - Wasabi Hot Cloud Storage
     - Cloudflare R2 Storage
     - Backblaze B2 (S3 & Native API)
     - Ceph Object Gateway (RADOS)
     - Generic S3-Compatible Storage
   - Live Connection Testing: Probe credentials and connectivity in background threads without freezing the interface.

2. **Panel-Based Dual-Pane File Transfers & Background Jobs**
   - Dual-pane layout (Left Panel ⇄ Right Panel) with independent remote and bucket/prefix navigation.
   - Central transfer actions:
     - `-> Copy` and `<- Copy` (Transfer selected items between endpoints)
     - `-> Move` and `<- Move` (Move items across remotes)
     - `Sync` (Synchronize source directory to destination with safety verification)
   - Real-Time Background Jobs View:
     - Asynchronous non-blocking worker engine.
     - Live progress bars, transfer speed (e.g. `24.5 MB/s`), ETA, and byte counters.
     - Job status tracking (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`).
     - Safe job cancellation and detailed telemetry logs.

3. **Object Storage Server & Bucket Management**
   - **Bucket Operations**: Create DNS-compliant S3 buckets with real-time name validation; inspect aggregated bucket size and object count.
   - **Object Operations**: Multi-selection delete, folder/prefix creation, file properties inspector, on-demand MD5 hash calculation.
   - **Live Filtering**: Instant search filter for objects within the current bucket/folder.

---

## Design & Aesthetics

- **Enterprise Modern Monochrome Theme**: Sleek dark slate aesthetic (`#141518`, `#1c1e23`, `#2b2e36`).
- **No Gradients**: Strictly flat, modern enterprise UI with crisp 1px borders.
- **Pure Outline Icons**: 100% procedural vector outline icons rendered via `QPainter` paths. Zero colored icons, zero emojis.

---

## NASA JPL The Power of 10 Safety Rules Compliance

The codebase strictly adheres to the 10 safety-critical rules formulated by Gerard J. Holzmann (NASA/JPL Laboratory for Reliable Software):

1. **Rule 1 (Simple Control Flow)**: Straightforward linear logic. No recursion, no `goto`, no complex branching.
2. **Rule 2 (Fixed Upper Bound on Loops)**: Every loop across parsing, queue processing, and I/O has statically determinable upper bounds (`MAX_ITEMS_PER_DIR`, `MAX_STATS_PARSE_LINES`, etc.).
3. **Rule 3 (Bounded Memory & Queues)**: Memory allocations and queues are statically bounded (`deque(maxlen=MAX_TRANSFER_QUEUE_SIZE)`, fixed buffer chunks).
4. **Rule 4 (Short Functions)**: Every function is under 60 lines of code. This is verified by an automated AST static analysis test (`tests/test_nasa_rules.py`).
5. **Rule 5 (High Assertion Density)**: Functions maintain high assertion density (average >= 2 assertions per function) verifying preconditions, invariants, and postconditions.
6. **Rule 6 (Minimal Data Scope)**: All variables are declared at the smallest possible scope.
7. **Rule 7 (Check Return Values)**: Non-void functions return typed `OperationResult` containers, and every return value is explicitly verified by callers.
8. **Rule 8 (No Metaprogramming)**: Transparent typing and explicit interfaces without dynamic runtime manipulation.
9. **Rule 9 (Reference & Structure Clarity)**: Typed Dataclasses with explicit types and field validations.
10. **Rule 10 (Strict Code Quality)**: Zero syntax errors, type-safe structures, and 100% unit test coverage on core routines.

---

## Project Structure

```
osb/
├── osb/
│   ├── core/
│   │   ├── constants.py       # NASA static upper bounds and timeouts
│   │   ├── models.py          # Strict dataclasses with assertions
│   │   ├── rclone_cli.py      # Low-level bounded rclone CLI execution
│   │   ├── config_mgr.py      # Remote configuration management & presets
│   │   ├── transfer_mgr.py    # Background transfer job queue & telemetry
│   │   └── utils.py           # Formatters and path validators
│   ├── gui/
│   │   ├── theme.py           # Clean enterprise monochrome stylesheet (no gradients)
│   │   ├── outline_icons.py   # Vector outline icon generator (QPainter)
│   │   ├── panel_browser.py   # Single storage browser with table & actions
│   │   ├── dual_panel.py      # Dual-pane container with transfer action strip
│   │   ├── jobs_view.py       # Bottom job queue with live progress & logs
│   │   ├── remote_dialog.py   # Rclone configuration modal & connection tester
│   │   ├── bucket_dialog.py   # Bucket creator & properties dialog
│   │   ├── file_details_dialog.py # Object metadata & MD5 checksum inspector
│   │   └── main_window.py     # Main application window
│   └── main.py                # Entrypoint & CLI runner
├── tests/
│   ├── test_nasa_rules.py     # AST static analyzer verifying Rules 4 & 5
│   ├── test_models.py         # Data models and assertion tests
│   ├── test_utils.py          # Path and size formatting tests
│   ├── test_outline_icons.py  # Vector outline icon rendering tests
│   ├── test_rclone_cli.py     # Real CLI execution tests
│   └── test_transfer_mgr.py   # Background queue and worker tests
├── run.sh                     # Executable launcher script
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- `rclone` (installed and available in `PATH`)
- `PyQt6`

### Running the Application

Launch via the bash runner:
```bash
./run.sh
```

Or directly via python:
```bash
python3 -m osb.main
```

### Running Tests

Run the complete test suite including the NASA JPL Power of 10 static analyzer:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
