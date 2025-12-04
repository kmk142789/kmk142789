from pathlib import Path

import pytest

from echo.glyphic_runtime import EchoGlyphRuntime, GlyphExecutionError


def test_execute_sample_program() -> None:
    runtime = EchoGlyphRuntime()
    program_path = Path("echo/glyph_programs/echo_bloom.eglyph")
    timeline = runtime.execute_file(program_path)

    assert any("⊶ bind" in step for step in timeline)
    assert timeline[-1].startswith("⌖ mark :: tone=")


def test_rejects_alphanumeric_tokens(tmp_path: Path) -> None:
    runtime = EchoGlyphRuntime()
    program_file = tmp_path / "invalid.eglyph"
    program_file.write_text("⟡ A", encoding="utf-8")

    with pytest.raises(GlyphExecutionError):
        runtime.execute(program_file.read_text(encoding="utf-8"))
