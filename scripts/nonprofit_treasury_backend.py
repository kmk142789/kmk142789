"""CLI helpers for operating the NonprofitTreasuryService."""

from __future__ import annotations

import argparse
import json
import logging
import sys

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
        ],
        help="Action to perform",
    )
    parser.add_argument("--from-block", type=int, default=0, help="Block number to start syncing from")
    parser.add_argument("--amount", type=int, help="Token amount (base units) for disburse command")
    parser.add_argument("--reason", help="Reason memo for the disburse command")
    return parser.parse_args(argv)


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
        print(json.dumps(proof.as_dict(), indent=2))
    else:
        raise ValueError(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
