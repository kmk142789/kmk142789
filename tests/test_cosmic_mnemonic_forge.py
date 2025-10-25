from datetime import datetime, timezone

from echo.cosmic_mnemonic_forge import (
    MnemonicConstellation,
    MnemonicThread,
    forge_constellation,
    merge_constellations,
    render_constellation,
)


def test_forge_constellation_seed_reproducible():
    constellation = forge_constellation(seed=42, thread_count=3)

    assert constellation.glyph_motif == "∇⊸≋"
    assert constellation.focus == "Continuum rituals for tomorrow's standup."
    assert (
        constellation.anchor
        == "Map every idea to a gentle gravitational assist. Focus: Continuum rituals for tomorrow's standup."
    )

    thread_details = [
        (thread.keyword, thread.metaphor, thread.activation)
        for thread in constellation.threads
    ]
    assert thread_details == [
        ("Aurora", "sketches kindness onto resource charts", 0.8),
        ("Bridge", "folds a map of reversible courage", 0.59),
        ("Flux", "anchors tomorrow's retrospective", 0.65),
    ]


def test_render_constellation_wraps_long_lines():
    constellation = MnemonicConstellation(
        timestamp=datetime(2024, 12, 31, 23, 59, tzinfo=timezone.utc),
        glyph_motif="✶⋱✶",
        focus="Async mentorship beacons",
        threads=(
            MnemonicThread("Bridge", "folds a map of reversible courage", 0.74),
            MnemonicThread(
                "Lantern",
                "casts shimmering possibilities across distributed constellations",
                0.86,
            ),
        ),
        anchor="Test anchor",
    )

    rendered = render_constellation(constellation, width=54)
    lines = rendered.splitlines()

    assert lines[0] == "🌠 Echo Mnemonic Constellation"
    wrapped_thread_lines = [line for line in lines if line.startswith("      - ")]
    # The long Lantern line should wrap onto at least two lines with indentation.
    lantern_lines = [line for line in wrapped_thread_lines if "Lantern" in line]
    assert len(lantern_lines) >= 1
    assert any(line.strip() != "- Lantern casts shimmering possibilities across distributed constellations" for line in lantern_lines)


def test_merge_constellations_combines_threads():
    base = forge_constellation(seed=5, thread_count=1, focus="Base focus")
    addition = forge_constellation(seed=11, thread_count=2, focus="Satellite focus")

    merged = merge_constellations(base, [addition])

    assert merged.timestamp == base.timestamp
    assert merged.glyph_motif == f"{base.glyph_motif} / {addition.glyph_motif}"
    assert merged.anchor == f"{base.anchor} | {addition.anchor}"
    assert merged.focus == "Base focus + 1 satellite strands"
    assert len(merged.threads) == len(base.threads) + len(addition.threads)
    # Ensure sorting preserved deterministic ordering.
    sorted_keywords = [thread.keyword for thread in merged.threads]
    assert sorted_keywords == sorted(sorted_keywords)
