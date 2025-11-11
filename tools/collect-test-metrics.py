#!/usr/bin/env python3
"""Aggregate cross-language test metrics for release reporting."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "out"
OUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUT_DIR / "test-metrics.json"


def _run_command(cmd: List[str], cwd: Path | None = None) -> Dict[str, Any]:
    """Run a shell command and capture metadata for the release report."""
    display = " ".join(cmd)
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        status = "passed"
        stdout = completed.stdout
    except subprocess.CalledProcessError as exc:  # pragma: no cover - debugging aid
        status = "failed"
        stdout = f"{exc.stdout}\n{exc.stderr}"
    return {
        "command": display,
        "cwd": str(cwd or ROOT),
        "status": status,
        "output": stdout.strip(),
    }


def _extract_pytest_totals(output: str) -> Dict[str, int]:
    match = re.search(r"collected (\\d+) items", output)
    total = int(match.group(1)) if match else 0
    passed_match = re.search(r"(\\d+) passed", output)
    failed_match = re.search(r"(\\d+) failed", output)
    skipped_match = re.findall(r"(\\d+) skipped", output)
    skipped = sum(int(value) for value in skipped_match) if skipped_match else 0
    return {
        "total": total,
        "passed": int(passed_match.group(1)) if passed_match else total - (int(failed_match.group(1)) if failed_match else 0),
        "failed": int(failed_match.group(1)) if failed_match else 0,
        "skipped": skipped,
    }


def _extract_go_totals(output: str) -> Dict[str, int]:
    passed = len(re.findall(r"ok\\s+", output))
    failed = len(re.findall(r"FAIL\\s+", output))
    return {
        "total": passed + failed,
        "passed": passed,
        "failed": failed,
        "skipped": 0,
    }


def main() -> int:
    runs: List[Dict[str, Any]] = []

    # Python tests
    python_cmd = [sys.executable, "-m", "pytest", "--maxfail", "1", "--disable-warnings"]
    python_run = _run_command(python_cmd)
    python_totals = _extract_pytest_totals(python_run["output"])
    python_run["totals"] = python_totals
    runs.append(python_run)

    # Node verification script (treated as smoke test)
    npm_cmd = ["npm", "test", "--silent"]
    npm_run = _run_command(npm_cmd)
    npm_run["totals"] = {
        "total": 1 if npm_run["status"] == "passed" else 1,
        "passed": 1 if npm_run["status"] == "passed" else 0,
        "failed": 0 if npm_run["status"] == "passed" else 1,
        "skipped": 0,
    }
    runs.append(npm_run)

    # Go client tests
    go_root = ROOT / "clients" / "go" / "echo_computer_agent_client"
    go_cmd = ["go", "test", "./..."]
    go_run = _run_command(go_cmd, cwd=go_root)
    go_run["totals"] = _extract_go_totals(go_run["output"])
    runs.append(go_run)

    aggregate = {
        "runs": runs,
        "summary": {
            "total": sum(run["totals"]["total"] for run in runs),
            "passed": sum(run["totals"]["passed"] for run in runs),
            "failed": sum(run["totals"]["failed"] for run in runs),
            "skipped": sum(run["totals"]["skipped"] for run in runs),
        },
    }

    OUTPUT_FILE.write_text(json.dumps(aggregate, indent=2))
    print(f"Wrote aggregated test metrics to {OUTPUT_FILE}")
    return 1 if any(run["status"] == "failed" for run in runs) else 0


if __name__ == "__main__":
    raise SystemExit(main())
