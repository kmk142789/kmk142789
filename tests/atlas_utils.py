from __future__ import annotations

from pathlib import Path


def write_sample_files(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / ".github").mkdir(parents=True, exist_ok=True)
    (root / "CONTROL.md").write_text(
        """
## Ownership + Inventory
- Bots: echo-attest-bot (attest-only)
- External: Cloudflare (API)
---
""".strip(),
        encoding="utf-8",
    )
    (root / "SECURITY.md").write_text(
        """
## Reporting
Contact us at security@example.org.

## Expectations
- Rotate secrets
""".strip(),
        encoding="utf-8",
    )
    (root / ".github" / "CODEOWNERS").write_text("* @echo-attest-bot\n", encoding="utf-8")
    (root / "docs" / "sample.md").write_text("Owners: @echo-attest-bot", encoding="utf-8")
