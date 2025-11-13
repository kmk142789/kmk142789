"""CLI entry point for the security audit framework."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import List

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:  # pragma: no cover - import guard
    sys.path.insert(0, str(CURRENT_DIR))

from audit_framework import AuditTarget, FrameworkConfig, SecurityAuditFramework


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["."], help="Paths to audit")
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional path to a JSON configuration file",
    )
    return parser.parse_args()


def load_config(path: Path | None) -> FrameworkConfig:
    if path is None:
        return FrameworkConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    return FrameworkConfig(
        severity_weights=data.get("severity_weights", FrameworkConfig().severity_weights),
        detectors=data.get("detectors"),
        fail_on_score=data.get("fail_on_score", 0.75),
        max_findings=data.get("max_findings"),
        notes=data.get("notes", []),
    )


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    targets: List[AuditTarget] = [AuditTarget(name=Path(path).name or path, path=path) for path in args.paths]
    framework = SecurityAuditFramework()
    signals = framework.run(targets, config)
    for target, target_signals in signals.items():
        print(f"=== {target} ===")
        for signal in target_signals:
            status = "ACTION REQUIRED" if signal.is_actionable(config.fail_on_score) else "monitor"
            print(
                f"[{status}] {signal.category} score={signal.score:.2f}: {signal.finding.description}"
            )
            if signal.recommendation:
                print(f" -> {signal.recommendation}")


if __name__ == "__main__":  # pragma: no cover
    main()
