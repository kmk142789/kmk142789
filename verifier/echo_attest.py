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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", required=True, help="Free-text attestation context")
    ap.add_argument("--signer-id", default=os.getenv("ECHO_SIGNER_ID", "echo-attest-bot"))
    args = ap.parse_args()

    digest = hashlib.sha256(args.context.encode("utf-8")).hexdigest()
    out = {
        "type": "echo_attestation",
        "ts": int(time.time()),
        "signer_id": args.signer_id,
        "context": args.context,
        "sha256": digest,
    }
    print(json.dumps(out, separators=(",", ":")))
    # Persist a local breadcrumb (optional)
    os.makedirs(".attest", exist_ok=True)
    with open(f".attest/{out['ts']}_{out['sha256'][:8]}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
