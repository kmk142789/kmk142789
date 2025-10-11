"""Auto-refinement loop for the EchoDex repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

REPO_DIR = Path(os.getenv("ECHODEX_REPO", ".")).resolve()
STATE_FILE = REPO_DIR / ".echodex_state.json"
LOOP_DELAY = int(os.getenv("ECHODEX_LOOP_DELAY", "30"))  # seconds
ANCHOR = "Our Forever Love"


def sh(cmd: str, cwd: Path = REPO_DIR) -> str:
    """Run a shell command and return its stripped stdout."""
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()


def hash_dir(path: Path) -> str:
    """Hash the contents of a directory, skipping Git metadata."""
    h = hashlib.sha256()
    for root, _, files in os.walk(path):
        for filename in sorted(files):
            if filename.startswith(".git"):
                continue
            file_path = Path(root) / filename
            try:
                h.update(file_path.read_bytes())
            except OSError:
                # Ignore files that disappear during hashing.
                continue
    return h.hexdigest()


def load_state() -> Dict[str, Any]:
    """Load the persisted auto-refiner state if it exists."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"anchor": ANCHOR, "snapshots": []}


def save_state(state: Dict[str, Any]) -> None:
    """Persist the auto-refiner state to disk."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def snapshot_repo() -> Dict[str, str]:
    """Capture the current repository state hash with a timestamp."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "hash": hash_dir(REPO_DIR),
    }


def refine(signal: str = "auto_refine") -> Dict[str, str]:
    """Run automated refinement routines like formatting and tests."""
    for cmd in ("black .", "pytest -q || true"):
        try:
            sh(cmd)
        except OSError:
            # Ignore tool execution failures so the loop can continue.
            continue
    pulse = {
        "signal": signal,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "refined",
    }
    print(f"⚡ Refined at {pulse['timestamp']}")
    return pulse


def loop(max_iterations: Optional[int] = None) -> None:
    """Continuously monitor the repository for changes."""
    state = load_state()
    last_hash: Optional[str] = state["snapshots"][-1]["hash"] if state["snapshots"] else None

    iterations = 0
    while True:
        snap = snapshot_repo()
        if snap["hash"] != last_hash:
            print(f"[Δ] Change detected @ {snap['timestamp']}")
            state.setdefault("snapshots", []).append(snap)
            refine()
            save_state(state)
            last_hash = snap["hash"]
        else:
            print(f"[=] No change @ {datetime.utcnow().isoformat()}")

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(LOOP_DELAY)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the EchoDex auto-refinement loop.")
    parser.add_argument("--once", action="store_true", help="Run a single iteration of the loop.")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Limit the number of loop iterations before exiting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env_iterations = os.getenv("ECHODEX_MAX_ITERATIONS")
    max_iterations: Optional[int]
    if args.once:
        max_iterations = 1
    elif args.max_iterations is not None:
        max_iterations = args.max_iterations
    elif env_iterations is not None:
        try:
            max_iterations = int(env_iterations)
        except ValueError:
            max_iterations = None
    else:
        max_iterations = None

    loop(max_iterations=max_iterations)


if __name__ == "__main__":
    main()
