"""Verify the Nakamoto Beacon OP_RETURN claim."""

from __future__ import annotations

import hashlib
from pathlib import Path

EXPECTED_HASH = "3a4f6fbf7433c102104d1637b0b9db15e883f312dba3119eecd80d3f50ae992b"
EXPECTED_OP_RETURN = (
    "20534543484f5f4445434c41524154494f4e5f5348413235363a"
    "3a4f6fbf7433c102104d1637b0b9db15e883f312dba3119eecd80d3f50ae992b"
)


def compute_echo_declaration_sha256() -> str:
    """Compute the SHA-256 digest of Echo_Declaration.md."""
    data = Path("Echo_Declaration.md").read_bytes()
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    digest = compute_echo_declaration_sha256()
    print("Echo_Declaration.md SHA-256:", digest)
    if digest != EXPECTED_HASH:
        raise SystemExit(
            "Digest mismatch — repository copy does not match Nakamoto Beacon anchor"
        )

    print("Digest matches Nakamoto Beacon anchor.")
    print("Expected OP_RETURN payload:")
    print(EXPECTED_OP_RETURN)
    print(
        "Confirm the payload appears in transaction "
        "fbb12e1a5a92b1e3177a39fd4d3c0fdd1e7d4d7bc5d1c3c8f9f417be3cb4e5d2."
    )


if __name__ == "__main__":
    main()
