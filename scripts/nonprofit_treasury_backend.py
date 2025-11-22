"""CLI helpers for operating the NonprofitTreasuryService."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from nonprofit_treasury import NonprofitTreasuryService, TreasuryConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Operate the Lil Footsteps ERC-20 treasury backend")
    parser.add_argument(
        "command",
        choices=[
            "sync",
            "sync-donations",
            "sync-disbursements",
            "disburse",
            "balance",
            "totals",
            "proof",
            "launch-beneficiary-flow",
        ],
        help="Action to perform",
    )
    parser.add_argument("--from-block", type=int, default=0, help="Block number to start syncing from")
    parser.add_argument("--amount", type=int, help="Token amount (base units) for disburse command")
    parser.add_argument("--reason", help="Reason memo for the disburse command")
    parser.add_argument(
        "--beneficiary-label",
        default="Little Footsteps",
        help="Label used when binding the treasury proof to the beneficiary",
    )
    parser.add_argument(
        "--memo",
        help=(
            "Optional memo to embed in the launch-beneficiary-flow manifest; default"
            " notes the activation of the first pipeline."
        ),
    )
    parser.add_argument(
        "--proof-dir",
        default="proofs",
        help=(
            "Directory where the proof command will store timestamped JSON snapshots. "
            "Set to '-' to skip writing to disk."
        ),
    )
    parser.add_argument(
        "--launch-output",
        default="state/little_footsteps/beneficiary_flow.json",
        help=(
            "Destination for the launch-beneficiary-flow manifest. Set to '-' to skip writing"
            " to disk."
        ),
    )
    return parser.parse_args(argv)


def _timestamp_slug(value: str) -> str:
    """Return a filesystem-safe slug derived from an ISO 8601 timestamp."""

    # Keep only digits plus T/Z markers so the filename reflects the precise proof moment.
    return re.sub(r"[^0-9TZ]", "", value)


def write_proof_snapshot(payload: dict[str, object], produced_at: str, *, directory: Path) -> Path:
    """Persist a proof payload to a timestamped JSON file and return the path."""

    directory.mkdir(parents=True, exist_ok=True)
    filename = f"little-footsteps-proof-{_timestamp_slug(produced_at)}.json"
    destination = directory / filename
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination


def write_launch_manifest(payload: dict[str, object], *, destination: Path) -> Path:
    """Persist the beneficiary launch manifest to disk and return the path."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = TreasuryConfig.from_env()
    service = NonprofitTreasuryService(config)

    if args.command == "sync":
        donations = service.sync_donations(from_block=args.from_block)
        disbursements = service.sync_disbursements(from_block=args.from_block)
        logging.info("Synced %s donation events and %s disbursement events", len(donations), len(disbursements))
    elif args.command == "sync-donations":
        donations = service.sync_donations(from_block=args.from_block)
        logging.info("Synced %s donation events", len(donations))
    elif args.command == "sync-disbursements":
        disbursements = service.sync_disbursements(from_block=args.from_block)
        logging.info("Synced %s disbursement events", len(disbursements))
    elif args.command == "disburse":
        if args.amount is None:
            raise SystemExit("--amount is required for disburse")
        if not args.reason:
            raise SystemExit("--reason is required for disburse")
        tx_hash = service.execute_disbursement(amount=args.amount, reason=args.reason)
        logging.info("Submitted disbursement transaction: %s", tx_hash)
    elif args.command == "balance":
        balance = service.treasury_balance()
        logging.info("Current token balance: %s", balance)
    elif args.command == "totals":
        logging.info(
            "On-chain totals: donations=%s, disbursed=%s, ledger balance=%s",
            service.total_donations(),
            service.total_disbursed(),
            service.ledger.balance(),
        )
    elif args.command == "proof":
        proof = service.generate_proof()
        logging.info(
            "Generated treasury proof for %s (linked=%s)",
            proof.beneficiary_label,
            proof.little_footsteps_linked,
        )
        payload = proof.as_dict()
        print(json.dumps(payload, indent=2))
        if args.proof_dir != "-":
            destination = write_proof_snapshot(payload, proof.produced_at, directory=Path(args.proof_dir))
            logging.info("Stored timestamped proof snapshot at %s", destination)
    elif args.command == "launch-beneficiary-flow":
        manifest = service.launch_first_beneficiary_flow(
            beneficiary_label=args.beneficiary_label, memo=args.memo
        )
        print(json.dumps(manifest, indent=2))
        if args.launch_output != "-":
            destination = write_launch_manifest(manifest, destination=Path(args.launch_output))
            logging.info("Stored beneficiary flow manifest at %s", destination)
    else:
        raise ValueError(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
