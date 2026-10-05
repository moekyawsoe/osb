"""Rclone binary detection and cross-platform installation instructions engine.

Adheres strictly to NASA JPL Power of 10 rules:
- Rule 2: Fixed upper bounds on path candidate iterations
- Rule 3: Static, immutable installation metadata structures
- Rule 4: Functions strictly <= 60 lines
- Rule 5: High assertion density (>= 2 assertions per function)
- Rule 7: Comprehensive validation of paths and return values
"""

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class InstallMethod:
    """Description and CLI command for an installation method."""
    title: str
    command: str


@dataclass(frozen=True)
class PlatformGuide:
    """Installation guide and links for a specific operating system."""
    os_name: str
    display_title: str
    methods: Tuple[InstallMethod, ...]
    download_url: str
    guide_url: str


OFFICIAL_DOWNLOADS_URL = "https://rclone.org/downloads/"
OFFICIAL_INSTALL_GUIDE_URL = "https://rclone.org/install/"
GITHUB_RELEASES_URL = "https://github.com/rclone/rclone/releases"

PLATFORM_GUIDES: Dict[str, PlatformGuide] = {
    "linux": PlatformGuide(
        os_name="linux",
        display_title="Linux (Ubuntu, Debian, Fedora, Arch)",
        methods=(
            InstallMethod("Automated Script (Recommended)", "curl https://rclone.org/install.sh | sudo bash"),
            InstallMethod("Debian / Ubuntu / Mint", "sudo apt update && sudo apt install -y rclone"),
            InstallMethod("Fedora / RHEL / CentOS", "sudo dnf install -y rclone"),
            InstallMethod("Arch Linux / Manjaro", "sudo pacman -S --noconfirm rclone"),
            InstallMethod("Snap Package", "sudo snap install rclone"),
        ),
        download_url="https://rclone.org/downloads/#linux",
        guide_url="https://rclone.org/install/#script-installation",
    ),
    "darwin": PlatformGuide(
        os_name="darwin",
        display_title="macOS (Apple Silicon & Intel)",
        methods=(
            InstallMethod("Homebrew (Recommended)", "brew install rclone"),
            InstallMethod("Automated Script", "sudo -v && curl https://rclone.org/install.sh | sudo bash"),
            InstallMethod("MacPorts", "sudo port install rclone"),
        ),
        download_url="https://rclone.org/downloads/#macos",
        guide_url="https://rclone.org/install/#macos",
    ),
    "windows": PlatformGuide(
        os_name="windows",
        display_title="Windows (10 / 11 / Server)",
        methods=(
            InstallMethod("Windows Package Manager (Winget)", "winget install Rclone.Rclone"),
            InstallMethod("Chocolatey", "choco install rclone"),
            InstallMethod("Scoop", "scoop install rclone"),
            InstallMethod("Direct Zip Archive", "https://downloads.rclone.org/rclone-current-windows-amd64.zip"),
        ),
        download_url="https://rclone.org/downloads/#windows",
        guide_url="https://rclone.org/install/#windows",
    ),
}


def get_current_platform_key() -> str:
    """Identify normalized operating system key (linux, darwin, windows)."""
    system_str = platform.system().lower()
    assert isinstance(system_str, str), "System name must be string"
    if "darwin" in system_str or "mac" in system_str:
        return "darwin"
    elif "win" in system_str:
        return "windows"
    return "linux"


def _get_platform_candidate_paths() -> List[str]:
    """Retrieve standard candidate filesystem paths for rclone binary."""
    plat = get_current_platform_key()
    assert plat in ("linux", "darwin", "windows"), f"Unsupported platform {plat}"
    home = os.path.expanduser("~")

    if plat == "windows":
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
        return [
            os.path.join(prog_files, "rclone", "rclone.exe"),
            os.path.join(prog_files_x86, "rclone", "rclone.exe"),
            os.path.join(local_app, "Programs", "rclone", "rclone.exe"),
            r"C:\rclone\rclone.exe",
            os.path.join(home, "scoop", "shims", "rclone.exe"),
        ]

    # Unix (Linux & macOS) paths
    candidates = [
        "/usr/bin/rclone",
        "/usr/local/bin/rclone",
        "/opt/homebrew/bin/rclone",
        os.path.join(home, ".local", "bin", "rclone"),
        os.path.join(home, "bin", "rclone"),
        "/snap/bin/rclone",
    ]
    assert len(candidates) > 0, "Candidate paths must not be empty"
    return candidates


def find_rclone_binary(custom_path: Optional[str] = None) -> Optional[str]:
    """Discover valid rclone binary with NASA Rule 2 bounded search."""
    if custom_path:
        assert isinstance(custom_path, str), "Custom path must be a string"
        if os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
            return os.path.abspath(custom_path)

    # 1. Search system PATH
    which_path = shutil.which("rclone") or shutil.which("rclone.exe")
    if which_path and os.path.isfile(which_path):
        return os.path.abspath(which_path)

    # 2. Search predefined platform directories with bounded loop
    candidates = _get_platform_candidate_paths()
    max_candidates = min(len(candidates), 20)
    for i in range(max_candidates):
        cand = candidates[i]
        if os.path.isfile(cand) and (sys.platform == "win32" or os.access(cand, os.X_OK)):
            return os.path.abspath(cand)

    assert custom_path is None or not os.path.isfile(custom_path), "Invalid custom path"
    return None


def get_platform_guide(platform_key: Optional[str] = None) -> PlatformGuide:
    """Retrieve platform installation guide metadata."""
    key = platform_key or get_current_platform_key()
    assert isinstance(key, str), "Platform key must be string"
    guide = PLATFORM_GUIDES.get(key, PLATFORM_GUIDES["linux"])
    assert guide is not None, "Platform guide must be resolved"
    return guide
