"""Utilities for verifying Ethereum wallet ownership and recording balances.

This module implements a small worker that reads pending wallet records from a
PostgreSQL database, verifies that each wallet provided a valid proof-of-control
signature, and snapshots the on-chain ETH balance.  The implementation is
defensive: we validate input, handle API errors gracefully, and store balances
as integer Wei amounts to avoid floating point precision issues.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import psycopg2
import psycopg2.extras
import requests
from eth_account.messages import encode_defunct
from eth_account.account import Account

# Number of rows processed per batch.
BATCH_SIZE = 100
# Delay between external API requests to avoid exhausting rate limits.
THROTTLE_SECONDS = 1.2
# Default location for proof-of-control message files.
DEFAULT_PROOFS_DIR = Path("proofs")


logger = logging.getLogger(__name__)


@dataclass
class WalletRecord:
    """Row returned from the ``wallets`` database table."""

    row_id: int
    address: str
    signature: str


class VerificationError(Exception):
    """Raised when a wallet cannot be verified."""


def verify_signature_eth(address: str, message: str, signature: str) -> bool:
    """Validate an Ethereum signature for the supplied message.

    Parameters
    ----------
    address:
        Expected wallet address.
    message:
        Message that should have been signed.
    signature:
        Hex-encoded signature.
    """

    try:
        encoded_message = encode_defunct(text=message)
        recovered = Account.recover_message(encoded_message, signature=signature)
    except Exception as exc:  # pragma: no cover - defensive safety net
        logger.warning("Failed to recover signature for %s: %s", address, exc)
        raise VerificationError("signature_recovery_failed") from exc

    return recovered.lower() == address.lower()


def get_eth_balance(address: str, api_key: str, session: Optional[requests.Session] = None) -> int:
    """Fetch the balance for ``address`` (in Wei) using the Etherscan API."""

    if session is None:
        session = requests.Session()

    params = {
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
        "apikey": api_key,
    }

    try:
        response = session.get("https://api.etherscan.io/api", params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise VerificationError("etherscan_request_failed") from exc

    payload = response.json()
    if payload.get("status") == "0":
        raise VerificationError(payload.get("message", "etherscan_error"))

    try:
        return int(payload["result"])
    except (KeyError, ValueError) as exc:
        raise VerificationError("invalid_balance_payload") from exc


def load_proof_message(address: str, proofs_dir: Path) -> str:
    """Return the proof-of-control message stored for ``address``."""

    proof_file = proofs_dir / f"{address}.txt"
    if not proof_file.exists():
        raise VerificationError("missing_proof_file")

    try:
        return proof_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise VerificationError("failed_to_read_proof") from exc


def fetch_pending_wallets(cursor: psycopg2.extensions.cursor) -> Iterable[WalletRecord]:
    """Yield wallets that still need verification."""

    cursor.execute(
        """
        SELECT id, address, signature
        FROM wallets
        WHERE verified = false
        LIMIT %s
        FOR UPDATE SKIP LOCKED
        """,
        (BATCH_SIZE,),
    )

    for row in cursor.fetchall():
        yield WalletRecord(row_id=row[0], address=row[1], signature=row[2])


def process_batch(
    conn: psycopg2.extensions.connection,
    api_key: str,
    proofs_dir: Path = DEFAULT_PROOFS_DIR,
    throttle_seconds: float = THROTTLE_SECONDS,
) -> int:
    """Process up to ``BATCH_SIZE`` wallet verifications.

    Returns the number of rows processed.
    """

    processed = 0
    session = requests.Session()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        for wallet in fetch_pending_wallets(cursor):
            try:
                message = load_proof_message(wallet.address, proofs_dir)
                if not verify_signature_eth(wallet.address, message, wallet.signature):
                    raise VerificationError("signature_mismatch")

                balance_wei = get_eth_balance(wallet.address, api_key, session=session)

                cursor.execute(
                    """
                    UPDATE wallets
                    SET verified = true,
                        balance_bigint = %s,
                        last_checked = NOW()
                    WHERE id = %s
                    """,
                    (balance_wei, wallet.row_id),
                )
                logger.info("Wallet %s verified; balance %s wei", wallet.address, balance_wei)
            except VerificationError as exc:
                cursor.execute(
                    """
                    UPDATE wallets
                    SET verified = false,
                        last_checked = NOW()
                    WHERE id = %s
                    """,
                    (wallet.row_id,),
                )
                logger.warning("Verification failed for %s: %s", wallet.address, exc)
            processed += 1
            conn.commit()
            time.sleep(throttle_seconds)

    return processed


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", help="PostgreSQL DSN", default=os.getenv("DATABASE_DSN"))
    parser.add_argument("--api-key", help="Etherscan API key", default=os.getenv("ETHERSCAN_API_KEY"))
    parser.add_argument(
        "--proofs-dir",
        type=Path,
        default=DEFAULT_PROOFS_DIR,
        help="Directory containing <address>.txt proof files",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    if not args.dsn:
        logger.error("Database DSN not provided")
        return 1

    if not args.api_key:
        logger.error("Etherscan API key not provided")
        return 1

    try:
        conn = psycopg2.connect(args.dsn)
    except psycopg2.Error as exc:
        logger.error("Failed to connect to database: %s", exc)
        return 1

    try:
        processed = process_batch(conn, args.api_key, args.proofs_dir)
        if processed == 0:
            logger.info("No pending wallets to verify")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
