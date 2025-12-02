"""Fingerprint and rarity coverage for :mod:`src.creative_loop`."""

from __future__ import annotations

from src.creative_loop import LoopSeed, compose_loop, generate_loop


def test_generate_loop_includes_fingerprint() -> None:
    """A generated loop should carry a fingerprint describing its rarity."""

    seed = LoopSeed(motif="signal", fragments=("beam", "halo"), pulses=2, seed=5)
    loop = generate_loop(seed)

    assert loop.fingerprint is not None
    assert loop.fingerprint.signature
    assert len(loop.fingerprint.accent_sparkline) == len(loop.diagnostics.accents)


def test_fingerprint_is_stable_for_same_seed() -> None:
    """Fingerprints should be deterministic for identical inputs."""

    seed = LoopSeed(motif="pulse", fragments=("glow",), pulses=3, seed=9)
    first = generate_loop(seed)
    second = generate_loop(seed)

    assert first.fingerprint is not None
    assert second.fingerprint is not None
    assert first.fingerprint.signature == second.fingerprint.signature


def test_markdown_output_surfaces_fingerprint() -> None:
    """Markdown output should surface the fingerprint summary."""

    seed = LoopSeed(motif="aurora", fragments=("echo",), pulses=1, seed=2)
    markdown = compose_loop(seed, format="markdown")

    assert "> Fingerprint: " in markdown
