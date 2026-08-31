"""Result records with automatic provenance capture.

Every measurement in this project is written through this module, so any number
can be traced back to the exact code, machine, and inputs that produced it.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = REPO_ROOT / "results" / "raw"

# Packages whose version can move a metric. Extend as you add them.
TRACKED_PACKAGES = ("numpy", "scipy", "torch", "hnswlib")


def _git(*args: str) -> str:
    """Run git in the repo; return stripped stdout, or '' if it fails."""
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def _git_info() -> dict[str, Any]:
    return {
        "sha": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(_git("status", "--porcelain")),
    }


def _proc_field(path: str, prefix: str) -> str | None:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def _physical_cores() -> int | None:
    """Count distinct (socket, core) pairs, so hyperthreads aren't double-counted."""
    try:
        pairs, socket = set(), None
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("physical id"):
                socket = line.split(":", 1)[1].strip()
            elif line.startswith("core id"):
                pairs.add((socket, line.split(":", 1)[1].strip()))
        return len(pairs) or None
    except OSError:
        return None


def _ram_bytes() -> int | None:
    raw = _proc_field("/proc/meminfo", "MemTotal")
    return int(raw.split()[0]) * 1024 if raw else None


def _environment() -> dict[str, Any]:
    packages = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            continue
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "kernel": platform.release(),
        "cpu_model": _proc_field("/proc/cpuinfo", "model name") or "unknown",
        "cores_physical": _physical_cores(),
        "cores_logical": os.cpu_count(),
        "ram_total_bytes": _ram_bytes(),
        "python_version": platform.python_version(),
        "packages": packages,
    }


@dataclass
class Metric:
    value: float
    ci_lower: float | None = None
    ci_upper: float | None = None


@dataclass
class ResultRecord:
    inputs: dict[str, Any]
    metrics: dict[str, Metric] = field(default_factory=dict)
    per_query: dict[str, dict[str, float]] = field(default_factory=dict)
    notes: str = ""

    # Captured automatically at construction time.
    schema_version: int = SCHEMA_VERSION
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    git: dict[str, Any] = field(default_factory=_git_info)
    environment: dict[str, Any] = field(default_factory=_environment)

    def write(self, directory: Path | None = None) -> Path:
        directory = Path(directory) if directory else DEFAULT_RESULTS_DIR
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.timestamp_utc[:10]}_{self.run_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2) + "\n")
        return path


def load(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())
