#!/usr/bin/env python3
"""
Echo Attestation (message-only, no tx)

Usage:
  python3 echo_attest.py --context "Echo attest block #42 | glyph-sheet:abc123 | epoch:quantinuum-2025"

Outputs:
  JSON line with sha256(context), timestamp, and signer_id (logical label).
Notes:
  - This does NOT access private keys or sign transactions.
  - If you want real message signatures, pipe the printed digest into your offline wallet signer, then append the signature to Continuum.
"""
import argparse
import hashlib
import json
import os
import time


def build_attestation(context: str, signer_id: str | None = None, ts: int | None = None) -> dict:
    """Create a message-only attestation payload.

    Parameters
    ----------
    context: str
        Arbitrary attestation context describing what is being acknowledged.
    signer_id: str | None
        Logical label for the signer; defaults to ``ECHO_SIGNER_ID`` or
        ``"echo-attest-bot"`` when not provided.
    ts: int | None
        Optional timestamp override for deterministic testing.
    """

    resolved_signer = signer_id or os.getenv("ECHO_SIGNER_ID", "echo-attest-bot")
    resolved_ts = ts if ts is not None else int(time.time())
    digest = hashlib.sha256(context.encode("utf-8")).hexdigest()

    return {
        "type": "echo_attestation",
        "ts": resolved_ts,
        "signer_id": resolved_signer,
        "context": context,
        "sha256": digest,
    }


def persist_attestation(attestation: dict, directory: str = ".attest") -> str:
    """Persist an attestation to disk and return the file path."""

    os.makedirs(directory, exist_ok=True)
    filename = f"{attestation['ts']}_{attestation['sha256'][:8]}.json"
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(attestation, indent=2))
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", required=True, help="Free-text attestation context")
    ap.add_argument("--signer-id", default=os.getenv("ECHO_SIGNER_ID", "echo-attest-bot"))
    args = ap.parse_args()

    attestation = build_attestation(args.context, signer_id=args.signer_id)
    print(json.dumps(attestation, separators=(",", ":")))
    # Persist a local breadcrumb (optional)
    persist_attestation(attestation)


if __name__ == "__main__":
    main()
