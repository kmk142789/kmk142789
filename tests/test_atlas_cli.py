from __future__ import annotations

import json
from pathlib import Path

from echo_atlas.cli import main


SAMPLE_CONTROL = """\
## Ownership + Inventory (names only; no secrets)
- Bots: echo-attest-bot
- External: Cloudflare
"""


def prepare_repo(root: Path) -> None:
    root.joinpath("CONTROL.md").write_text(SAMPLE_CONTROL, encoding="utf-8")
    root.joinpath("SECURITY.md").write_text("Security contact", encoding="utf-8")
    gh = root / ".github"
    gh.mkdir()
    gh.joinpath("CODEOWNERS").write_text("* @kmk142789", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    docs.joinpath("index.md").write_text("# Index", encoding="utf-8")


def test_cli_sync_and_show(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    exit_code = main(["--root", str(tmp_path), "atlas", "sync"])
    assert exit_code == 0
    report = tmp_path / "docs" / "ATLAS_REPORT.md"
    assert report.exists()
    data = report.read_text(encoding="utf-8")
    assert "Echo Atlas Summary" in data

    exit_code = main(["--root", str(tmp_path), "atlas", "show", "--who", "kmk142789"])
    assert exit_code in (0, 1)
