from __future__ import annotations

from pathlib import Path

from echo_atlas.ingest import default_importers, run_importers
from echo_atlas.importers.control import ControlImporter
from echo_atlas.importers.codeowners import CodeownersImporter
from echo_atlas.importers.docs import DocsImporter
from echo_atlas.importers.security import SecurityImporter


def _write_sample_files(root: Path) -> None:
    root.joinpath("CONTROL.md").write_text(
        """
## Ownership + Inventory (names only; no secrets)
- Bots: echo-attest-bot (attest-only)
- External: Cloudflare (API)
""",
        encoding="utf-8",
    )
    root.joinpath("SECURITY.md").write_text("Security contact: security@example.org", encoding="utf-8")
    gh = root / ".github"
    gh.mkdir()
    gh.joinpath("CODEOWNERS").write_text("* @kmk142789", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    docs.joinpath("sample.md").write_text("# Sample Doc", encoding="utf-8")


def test_default_importers_collect_nodes(tmp_path: Path) -> None:
    _write_sample_files(tmp_path)
    importers = default_importers(tmp_path)
    batch = run_importers(importers)
    names = {node.name for node in batch.nodes}
    assert "echo-attest-bot (attest-only)" in names
    assert "Cloudflare (API)" in names
    assert any(edge.relation.value == "MENTIONS" for edge in batch.edges)
