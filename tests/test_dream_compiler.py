from pathlib import Path

from echo.dreams import DreamCompiler


POEM = """Spin the loom and forge the flame\nDreaming bytes from woven name."""


def test_dream_compiler_creates_plan_and_files(tmp_path: Path) -> None:
    compiler = DreamCompiler(base_path=tmp_path)
    result = compiler.compile(POEM, dry_run=True)
    assert result.slug.startswith("dream_")
    assert len(result.plan) >= 3

    result_live = compiler.compile(POEM, dry_run=False)
    for dream_file in result_live.files:
        assert dream_file.path.exists()
        compile(dream_file.content, str(dream_file.path), "exec")

    diff_signature = compiler.diff_signature(result_live)
    assert "metadata.json" in diff_signature
