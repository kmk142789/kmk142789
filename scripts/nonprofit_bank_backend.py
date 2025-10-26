"""CLI helpers for operating the NonprofitBankService."""

from __future__ import annotations

import argparse
import logging
import sys

from nonprofit_bank import BankConfig, NonprofitBankService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Operate the Lil Footsteps nonprofit bank backend")
    parser.add_argument("command", choices=["sync", "payout", "balance"], help="Action to perform")
    parser.add_argument("--from-block", type=int, default=0, help="Block number to start syncing from")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = BankConfig.from_env()
    service = NonprofitBankService(config)

    if args.command == "sync":
        events = service.sync_deposits(from_block=args.from_block)
        logging.info("Synced %s deposit events", len(events))
    elif args.command == "payout":
        tx_hash = service.trigger_payout()
        logging.info("Triggered payout: %s", tx_hash)
    elif args.command == "balance":
        balance = service.current_balance()
        logging.info("Current smart-contract balance: %s wei", balance)
    else:
        raise ValueError(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
