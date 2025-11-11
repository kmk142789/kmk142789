from pathlib import Path

from compliance.engine import run


def test_engine_writes_report(tmp_path):
    output_dir = tmp_path / "reports"
    result = run(Path("identity"), output_dir)

    assert (output_dir / "CONTRADICTIONS.md").exists()
    assert (output_dir / "authority_flow.mmd").exists()
    assert result.matrix["Fail"] >= 1
    assert result.matrix["Soft"] >= 1
    markdown = (output_dir / "CONTRADICTIONS.md").read_text(encoding="utf-8")
    assert "Summary Matrix" in markdown
    assert "Fix-it Plan" in markdown
