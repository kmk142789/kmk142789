"""Bootstrap EOAG continuous audit state."""

from __future__ import annotations

import argparse
import json

from governance.eoag import bootstrap_eoag_state


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap EOAG operational state")
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format",
    )
    args = parser.parse_args()

    payload = bootstrap_eoag_state()

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    print("EOAG operational state initialized")
    print(f"- Registry: {payload['registry']['hooks'].__len__()} hooks")
    print(f"- Ledger: {payload['ledger_path']}")
    print(f"- Findings: {payload['findings_path']}")
    print(f"- Escalations: {payload['escalations_path']}")


if __name__ == "__main__":
    main()
