"""Write the environment and workload identity alongside benchmark artifacts."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def hardware_identity() -> dict[str, str | int | None]:
    cpu_model = None
    try:
        if sys.platform == "darwin":
            cpu_model = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
            ).strip()
        elif sys.platform == "linux":
            cpu_model = next(
                (
                    line.partition(":")[2].strip()
                    for line in Path("/proc/cpuinfo").read_text().splitlines()
                    if line.startswith("model name")
                ),
                None,
            )
    except (OSError, subprocess.CalledProcessError):
        pass
    return {"cpu_model": cpu_model, "logical_cpus": os.cpu_count()}


def write_metadata(output: Path, instrument: str) -> None:
    root = Path(__file__).resolve().parents[2]
    suite = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(suite.rglob("*")):
        if path.suffix in {".py", ".graphql"}:
            digest.update(path.relative_to(suite).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root, text=True
        ).strip()
    )
    metadata = {
        "suite_version": 2,
        "source_revision": revision,
        "worktree_dirty": dirty,
        "suite_sha256": digest.hexdigest(),
        "lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "instrument": instrument,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hardware": hardware_identity(),
        "gc_policy": "pytest-codspeed disables cyclic GC inside measurement",
        "cache_policy": "explicit per-round setup for cache workloads; see README",
        "dependencies": dict(
            sorted(
                (distribution.metadata["Name"], distribution.version)
                for distribution in importlib.metadata.distributions()
            )
        ),
        "runner": {
            key: os.environ.get(key)
            for key in (
                "RUNNER_NAME",
                "RUNNER_OS",
                "RUNNER_ARCH",
                "ImageOS",
                "ImageVersion",
                "GITHUB_REPOSITORY",
                "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT",
            )
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--instrument", required=True, choices=["simulation", "walltime", "memory"]
    )
    args = parser.parse_args()
    write_metadata(args.output, args.instrument)
