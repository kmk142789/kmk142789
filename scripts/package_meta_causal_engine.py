"""Package manifest generator for the meta-causal engine rollout."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from echo.deployment_meta_causal import load_meta_causal_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Package the meta-causal engine manifest")
    parser.add_argument(
        "--output",
        default="dist/meta_causal_engine/package.json",
        help="Path to write the package manifest (default: dist/meta_causal_engine/package.json)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = load_meta_causal_config()
    payload = {
        "engine": "meta-causal-engine",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": config.to_dict(),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Meta-causal engine package manifest written to {output_path}")


if __name__ == "__main__":
    main()
