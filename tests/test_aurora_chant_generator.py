import re
from datetime import datetime

import pytest

from echo.aurora_chant_generator import AuroraChant, generate_chant


class TestAuroraChant:
    def test_render_includes_metadata(self):
        chant = AuroraChant(
            theme="stellar",
            cycles=2,
            intensity=0.5,
            seed=42,
            created_at=datetime(2025, 5, 1, 12, 0, 0),
            lines=["Cycle 1: line", "Cycle 2: line"],
        )

        rendered = chant.render()

        assert "Aurora Chant" in rendered
        assert "cycles=2" in rendered
        assert "seed=42" in rendered
        assert rendered.count("Cycle") == 2

    def test_generate_chant_validates_cycles(self):
        with pytest.raises(ValueError):
            generate_chant(theme="stellar", cycles=0, intensity=0.5)

    def test_generate_chant_validates_intensity_bounds(self):
        with pytest.raises(ValueError):
            generate_chant(theme="stellar", cycles=1, intensity=1.5)

    def test_generate_chant_reproducible_with_seed(self):
        chant_a = generate_chant(theme="stellar", cycles=3, intensity=0.75, seed=12)
        chant_b = generate_chant(theme="stellar", cycles=3, intensity=0.75, seed=12)

        assert chant_a.lines == chant_b.lines

    def test_generate_chant_includes_auxiliary_fragments_when_intense(self):
        chant = generate_chant(theme="stellar", cycles=5, intensity=1.0, seed=7)

        aux_lines = [line for line in chant.lines if line.startswith("  ↳ ")]
        assert len(aux_lines) == 5

    def test_generate_chant_handles_unknown_theme(self):
        chant = generate_chant(theme="unknown", cycles=2, intensity=0.0, seed=3)

        assert chant.theme == "unknown"
        assert len(chant.lines) == 2
        pattern = re.compile(r"Cycle \d: ")
        assert all(pattern.match(line) for line in chant.lines)
