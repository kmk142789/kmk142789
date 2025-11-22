"""Bootstrap the Sovereign Ledger amendment credential registry.

This script issues verifiable credential payloads for each ratified
amendment text and appends them to the Sovereign Ledger registry. It is
idempotent for identical content because credential IDs incorporate the
content digest.
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ledger.sovereign_ledger_layer import SovereignLedgerLayer


def main() -> None:
    layer = SovereignLedgerLayer(
        registry_path=Path("state/sovereign_ledger/amendment_registry.jsonl"),
        credential_dir=Path("proofs/amendment_credentials"),
    )

    amendments = [
        ("I", Path("echo_digital_sovereignty_charter_amendment_I.md"), "The Echo–Little Footsteps Real-Time Transparency Mandate"),
        ("II", Path("echo_digital_sovereignty_charter_amendment_II.md"), "The Beneficiary Rights & Care Mandate"),
        ("III", Path("echo_digital_sovereignty_charter_amendment_III.md"), "The Bridge Federation & Credential Anchor Mandate"),
    ]

    for amendment_id, path, title in amendments:
        if not path.exists():
            raise FileNotFoundError(f"Missing amendment text: {path}")
        layer.issue_amendment_credential(
            amendment_path=path,
            amendment_id=amendment_id,
            title=title,
            issuer="Echo Constitutional Assembly",
            ledger_anchor=f"echo-sovereign-ledger:amendment-{amendment_id.lower()}",
        )


if __name__ == "__main__":
    main()
