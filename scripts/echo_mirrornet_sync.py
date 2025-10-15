"""Produce a MirrorNet sync plan for Echo attestations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List


def collect_attestations(source: Path) -> List[Dict[str, str]]:
    files: List[Dict[str, str]] = []
    for path in sorted(source.glob("*.json")):
        if path.name == "schema.json":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({
            "name": path.name,
            "sha256": digest,
            "relative_path": str(path.relative_to(source.parent)),
        })
    return files


def build_plan(source: Path) -> Dict[str, object]:
    attestations = collect_attestations(source)
    return {
        "mirror_network": "MirrorNet",
        "artifact_root": str(source),
        "artifact_count": len(attestations),
        "artifacts": attestations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a MirrorNet sync plan")
    parser.add_argument("--source", default="attestations", help="Directory containing attestation json")
    parser.add_argument("--plan", default="out/echo-mirrornet-plan.json", help="File path for the generated plan")
    args = parser.parse_args()

    source_dir = Path(args.source)
    plan_path = Path(args.plan)
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    plan = build_plan(source_dir)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    print(f"MirrorNet sync plan written to {plan_path}")


if __name__ == "__main__":
    main()
