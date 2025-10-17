"""Command-line interface for Pulse Narrator."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from .narrator import PulseNarrator
from .schemas import NarrativeInputs


def _load_inputs(path: str) -> NarrativeInputs:
    with open(path, "r", encoding="utf-8") as handle:
        raw: Dict[str, Any] = json.load(handle)
    if "timestamp" in raw and isinstance(raw["timestamp"], str):
        raw["timestamp"] = datetime.fromisoformat(raw["timestamp"])
    return NarrativeInputs(**raw)


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="echo-cli pulse narrator")
    parser.add_argument("--style", choices=["poem", "log"], default="poem")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--inputs", required=True, help="Path to JSON with NarrativeInputs fields")

    args = parser.parse_args(argv)

    inputs = _load_inputs(args.inputs)
    artifact = PulseNarrator().render(inputs, style=args.style, seed=args.seed)

    if args.save:
        os.makedirs("docs/narratives", exist_ok=True)
        filename = f"docs/narratives/{inputs.snapshot_id[:8]}_{artifact.sha256[:8]}_{args.style}.md"
        with open(filename, "w", encoding="utf-8") as output:
            output.write(artifact.body_md)
        print(json.dumps({"path": filename, "sha256": artifact.sha256}, indent=2))
    else:
        print(artifact.body_md)


if __name__ == "__main__":
    main()
